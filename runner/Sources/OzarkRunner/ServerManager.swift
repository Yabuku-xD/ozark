import Foundation
import AppKit
import Combine

struct RunSummary: Identifiable, Codable {
    var id: String
    var score: Int
    var status: String
    var summary: String
    var scenarioCount: Int
    var passedCount: Int
    var failedCount: Int
    var evalPassed: Bool
    var evalFailedCount: Int
    var gatePassed: Bool
}

struct LiveTestResult: Codable, Identifiable {
    var id: String { scenario_name + String(latency_ms) }
    var scenario_name: String
    var scenario_type: String
    var passed: Bool
    var score: Int
    var called_tools: [String]
    var latency_ms: Int
    var failures: [String]
}

struct IssueSummary: Identifiable, Codable {
    var id: String
    var title: String
    var severity: String
    var status: String
    var occurrenceCount: Int
}

struct DatasetSummary: Identifiable, Codable {
    var id: String
    var name: String
    var itemCount: Int
    var source: String
}

enum ServerState: Equatable {
    case stopped
    case starting
    case running(pid: Int32)
    case error(String)

    var isRunning: Bool {
        if case .running = self { return true }
        return false
    }

    var isStarting: Bool {
        if case .starting = self { return true }
        return false
    }

    var label: String {
        switch self {
        case .stopped: return "Stopped"
        case .starting: return "Starting"
        case .running: return "Running"
        case .error(let message): return "Error: \(message)"
        }
    }
}

@MainActor
final class ServerManager: ObservableObject {
    @Published var state: ServerState = .stopped
    @Published var logs: [String] = []
    @Published var liveTestResults: [LiveTestResult] = []
    @Published var issues: [IssueSummary] = []
    @Published var datasets: [DatasetSummary] = []
    @Published var lastRun: RunSummary?
    @Published var releaseReportMarkdown: String = ""
    @Published var isLiveTesting: Bool = false
    @Published var liveTestProgress: (completed: Int, total: Int) = (0, 0)

    let projectRoot: URL
    private var process: Process?
    private var outputPipe: Pipe?
    private var errorPipe: Pipe?
    private var liveTestTask: URLSessionDataTask?
    private let baseURL = URL(string: "http://127.0.0.1:8787")!

    init() {
        if let envRoot = ProcessInfo.processInfo.environment["OZARK_PROJECT_ROOT"] {
            projectRoot = URL(fileURLWithPath: envRoot)
        } else {
            projectRoot = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).deletingLastPathComponent()
        }
    }

    func start(agentPath: URL?, scenarioCount: Int, agentType: String) {
        guard !state.isRunning && !state.isStarting else { return }
        state = .starting
        logs = []
        appendLog("Starting Ozark server...")

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        proc.arguments = ["python3", "-m", "backend.server"]
        proc.currentDirectoryURL = projectRoot

        var env = ProcessInfo.processInfo.environment
        env["PORT"] = "8787"
        env["OZARK_SCENARIO_COUNT"] = String(scenarioCount)
        env["OZARK_AGENT_TYPE"] = agentType
        env["OZARK_PROJECT_ROOT"] = projectRoot.path
        if let agentPath = agentPath {
            env["OZARK_AGENT_PATH"] = agentPath.path
        }
        proc.environment = env

        let outPipe = Pipe()
        let errPipe = Pipe()
        proc.standardOutput = outPipe
        proc.standardError = errPipe
        outputPipe = outPipe
        errorPipe = errPipe

        outPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            guard let text = String(data: handle.availableData, encoding: .utf8), !text.isEmpty else { return }
            Task { @MainActor in self?.appendLog(text.trimmingCharacters(in: .whitespacesAndNewlines)) }
        }
        errPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            guard let text = String(data: handle.availableData, encoding: .utf8), !text.isEmpty else { return }
            Task { @MainActor in self?.appendLog("[err] " + text.trimmingCharacters(in: .whitespacesAndNewlines)) }
        }
        proc.terminationHandler = { [weak self] process in
            Task { @MainActor in
                guard let self = self else { return }
                if process.terminationStatus == 0 {
                    self.state = .stopped
                } else {
                    self.state = .error("Server exited with code \(process.terminationStatus)")
                }
            }
        }

        do {
            try proc.run()
            process = proc
            appendLog("Server process started with pid \(proc.processIdentifier)")
            Task {
                try? await Task.sleep(nanoseconds: 1_250_000_000)
                if proc.isRunning {
                    state = .running(pid: proc.processIdentifier)
                    refreshDashboard()
                }
            }
        } catch {
            state = .error(error.localizedDescription)
            appendLog("Failed to start: \(error.localizedDescription)")
        }
    }

    func stop() {
        liveTestTask?.cancel()
        process?.terminate()
        process = nil
        outputPipe?.fileHandleForReading.readabilityHandler = nil
        errorPipe?.fileHandleForReading.readabilityHandler = nil
        outputPipe = nil
        errorPipe = nil
        state = .stopped
        appendLog("Server stopped")
    }

    func openInBrowser() {
        NSWorkspace.shared.open(baseURL)
    }

    func runSimulation(agentID: String = "sample-support-agent", scenarioCount: Int, agentType: String) {
        guard state.isRunning else { return }
        appendLog("Running simulation: \(scenarioCount) scenarios")
        post("/api/runs", body: ["agent_id": agentID, "scenario_count": scenarioCount, "agent_type": agentType]) { [weak self] json in
            self?.handleRunResponse(json)
        }
    }

    func startLiveTest(endpoint: String, scenarioCount: Int, agentType: String) {
        guard state.isRunning else { return }
        isLiveTesting = true
        liveTestProgress = (0, scenarioCount)
        liveTestResults = []
        appendLog("Starting live test against \(endpoint)")
        post("/api/runs/live", body: ["endpoint": endpoint, "scenario_count": scenarioCount, "agent_type": agentType]) { [weak self] json in
            guard let self = self else { return }
            self.isLiveTesting = false
            self.handleRunResponse(json)
            self.liveTestResults = self.parseLiveResults(json)
            self.liveTestProgress = (self.liveTestResults.count, self.liveTestResults.count)
            self.appendLog("Live test complete: \(self.liveTestResults.filter(\.passed).count)/\(self.liveTestResults.count) passed")
        }
    }

    func refreshDashboard() {
        guard state.isRunning else { return }
        get("/api/issues?status=open") { [weak self] json in
            self?.issues = Self.parseIssues(json)
        }
        get("/api/datasets") { [weak self] json in
            self?.datasets = Self.parseDatasets(json)
        }
    }

    private func handleRunResponse(_ json: [String: Any]) {
        guard let run = json["run"] as? [String: Any] else { return }
        let evalReport = json["eval_report"] as? [String: Any]
        let gate = json["gate"] as? [String: Any]
        let summary = RunSummary(
            id: run["id"] as? String ?? "",
            score: run["score"] as? Int ?? 0,
            status: run["status"] as? String ?? "unknown",
            summary: run["summary"] as? String ?? "",
            scenarioCount: run["scenario_count"] as? Int ?? 0,
            passedCount: run["passed_count"] as? Int ?? 0,
            failedCount: run["failed_count"] as? Int ?? 0,
            evalPassed: evalReport?["passed"] as? Bool ?? true,
            evalFailedCount: evalReport?["failed_count"] as? Int ?? 0,
            gatePassed: gate?["passed"] as? Bool ?? true
        )
        lastRun = summary
        appendLog("Run \(summary.id): score \(summary.score), \(summary.passedCount)/\(summary.scenarioCount) passed")
        get("/api/reports/\(summary.id)?format=md") { [weak self] reportJSON in
            self?.releaseReportMarkdown = reportJSON["markdown"] as? String ?? ""
        }
        refreshDashboard()
    }

    private func parseLiveResults(_ json: [String: Any]) -> [LiveTestResult] {
        guard let run = json["run"] as? [String: Any], let results = run["results"] as? [[String: Any]] else { return [] }
        return results.map { result in
            LiveTestResult(
                scenario_name: result["scenario_name"] as? String ?? "",
                scenario_type: result["scenario_type"] as? String ?? "",
                passed: result["passed"] as? Bool ?? false,
                score: result["score"] as? Int ?? 0,
                called_tools: result["called_tools"] as? [String] ?? [],
                latency_ms: result["latency_ms"] as? Int ?? 0,
                failures: result["failures"] as? [String] ?? []
            )
        }
    }

    private static func parseIssues(_ json: [String: Any]) -> [IssueSummary] {
        guard let rows = json["issues"] as? [[String: Any]] else { return [] }
        return rows.map { row in
            IssueSummary(
                id: row["id"] as? String ?? "",
                title: row["title"] as? String ?? "",
                severity: row["severity"] as? String ?? "medium",
                status: row["status"] as? String ?? "open",
                occurrenceCount: row["occurrence_count"] as? Int ?? 0
            )
        }
    }

    private static func parseDatasets(_ json: [String: Any]) -> [DatasetSummary] {
        guard let rows = json["datasets"] as? [[String: Any]] else { return [] }
        return rows.map { row in
            DatasetSummary(
                id: row["id"] as? String ?? "",
                name: row["name"] as? String ?? "",
                itemCount: row["item_count"] as? Int ?? 0,
                source: row["source"] as? String ?? ""
            )
        }
    }

    private func get(_ path: String, completion: @escaping ([String: Any]) -> Void) {
        request(path: path, method: "GET", body: nil, completion: completion)
    }

    private func post(_ path: String, body: [String: Any], completion: @escaping ([String: Any]) -> Void) {
        request(path: path, method: "POST", body: body, completion: completion)
    }

    private func request(path: String, method: String, body: [String: Any]?, completion: @escaping ([String: Any]) -> Void) {
        var request = URLRequest(url: baseURL.appendingPathComponent(path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))))
        request.httpMethod = method
        request.timeoutInterval = 180
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let body = body {
            request.httpBody = try? JSONSerialization.data(withJSONObject: body)
        }
        URLSession.shared.dataTask(with: request) { [weak self] data, _, error in
            Task { @MainActor in
                if let error = error {
                    self?.appendLog("Request failed: \(error.localizedDescription)")
                    return
                }
                guard let data = data else {
                    self?.appendLog("Request returned no data")
                    return
                }
                do {
                    let object = try JSONSerialization.jsonObject(with: data)
                    if let json = object as? [String: Any] {
                        completion(json)
                    }
                } catch {
                    self?.appendLog("Response parse failed: \(error.localizedDescription)")
                }
            }
        }.resume()
    }

    private func appendLog(_ message: String) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        logs.append("[\(timestamp)] \(message)")
        if logs.count > 250 {
            logs.removeFirst(logs.count - 250)
        }
    }

    deinit {
        liveTestTask?.cancel()
        process?.terminate()
    }
}
