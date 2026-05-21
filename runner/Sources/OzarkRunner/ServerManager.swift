import Foundation
import AppKit
import Combine

struct LiveTestResult: Codable, Identifiable {
    var id: String { UUID().uuidString }
    var scenario_name: String
    var scenario_type: String
    var passed: Bool
    var score: Int
    var called_tools: [String]
    var latency_ms: Int
    var failures: [String]
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
        case .starting: return "Starting…"
        case .running: return "Running"
        case .error(let msg): return "Error: \(msg)"
        }
    }

    var dotColor: String {
        switch self {
        case .stopped: return "stopped"
        case .starting: return "starting"
        case .running: return "running"
        case .error: return "error"
        }
    }
}

@MainActor
class ServerManager: ObservableObject {
    @Published var state: ServerState = .stopped
    @Published var logs: [String] = []
    @Published var liveTestResults: [LiveTestResult] = []
    @Published var isLiveTesting: Bool = false
    @Published var liveTestLiveResult: LiveTestResult?
    @Published var liveTestProgress: (completed: Int, total: Int) = (0, 0)

    private var process: Process?
    private var outputPipe: Pipe?
    private var errorPipe: Pipe?
    private var liveTestTask: URLSessionDataTask?

    private var projectRoot: URL {
        let runnerDir = Bundle.main.bundleURL
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()

        if FileManager.default.fileExists(atPath: runnerDir.appendingPathComponent("backend").path) {
            return runnerDir
        }

        if let envRoot = ProcessInfo.processInfo.environment["OZARK_PROJECT_ROOT"] {
            return URL(fileURLWithPath: envRoot)
        }

        return URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    }

    func start(agentPath: URL?, scenarioCount: Int, agentType: String) {
        guard !state.isRunning && !state.isStarting else { return }

        state = .starting
        logs = []
        appendLog("Starting Ozark server...")

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        proc.arguments = ["python3", "-c", "from backend.server import main; main()"]
        proc.currentDirectoryURL = projectRoot

        var env = ProcessInfo.processInfo.environment
        env["PORT"] = "8787"
        if let agentPath = agentPath {
            env["OZARK_AGENT_PATH"] = agentPath.path
        }
        env["OZARK_SCENARIO_COUNT"] = String(scenarioCount)
        env["OZARK_AGENT_TYPE"] = agentType
        proc.environment = env

        let outPipe = Pipe()
        proc.standardOutput = outPipe
        outputPipe = outPipe

        let errPipe = Pipe()
        proc.standardError = errPipe
        errorPipe = errPipe

        outPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let line = String(data: data, encoding: .utf8) else { return }
            Task { @MainActor [weak self] in
                self?.appendLog(line.trimmingCharacters(in: .whitespacesAndNewlines))
                if line.contains("running at") {
                    self?.state = .running(pid: proc.processIdentifier)
                }
            }
        }

        errPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let line = String(data: data, encoding: .utf8) else { return }
            Task { @MainActor [weak self] in
                self?.appendLog("[err] \(line.trimmingCharacters(in: .whitespacesAndNewlines))")
            }
        }

        proc.terminationHandler = { [weak self] proc in
            Task { @MainActor [weak self] in
                if proc.terminationStatus != 0 && self?.state.isRunning != true {
                    self?.state = .error("Server exited with code \(proc.terminationStatus)")
                } else {
                    self?.state = .stopped
                }
                self?.appendLog("Server stopped (exit code \(proc.terminationStatus))")
            }
        }

        do {
            try proc.run()
            process = proc
            appendLog("Server process started (PID: \(proc.processIdentifier))")

            Task {
                try? await Task.sleep(nanoseconds: 2_500_000_000)
                if case .starting = self.state {
                    if proc.isRunning {
                        self.state = .running(pid: proc.processIdentifier)
                    }
                }
            }
        } catch {
            state = .error(error.localizedDescription)
            appendLog("Failed to start: \(error.localizedDescription)")
        }
    }

    func stop() {
        liveTestTask?.cancel()
        liveTestTask = nil
        isLiveTesting = false

        guard let proc = process, proc.isRunning else {
            state = .stopped
            return
        }

        appendLog("Stopping server...")
        proc.terminate()

        Task {
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            if proc.isRunning {
                proc.interrupt()
                appendLog("Force killed server")
            }
        }

        process = nil
        outputPipe = nil
        errorPipe = nil
    }

    func openInBrowser() {
        guard let url = URL(string: "http://127.0.0.1:8787") else { return }
        NSWorkspace.shared.open(url)
    }

    func startLiveTest(endpoint: String, scenarioCount: Int, agentType: String) {
        guard !isLiveTesting else { return }
        guard let url = URL(string: "http://127.0.0.1:8787/api/runs/live") else {
            appendLog("Invalid server URL")
            return
        }

        isLiveTesting = true
        liveTestResults = []
        liveTestLiveResult = nil
        liveTestProgress = (0, scenarioCount)
        appendLog("Starting live test against \(endpoint)...")

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 120

        let body: [String: Any] = [
            "endpoint": endpoint,
            "scenario_count": scenarioCount,
            "agent_type": agentType,
        ]
        request.httpBody = try? JSONSerialization.data(withJSONObject: body)

        let task = URLSession.shared.dataTask(with: request) { [weak self] data, response, error in
            Task { @MainActor [weak self] in
                guard let self = self else { return }
                self.isLiveTesting = false

                if let error = error {
                    self.appendLog("Live test error: \(error.localizedDescription)")
                    return
                }

                guard let data = data else {
                    self.appendLog("Live test: no data received")
                    return
                }

                do {
                    if let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let run = json["run"] as? [String: Any],
                       let results = run["results"] as? [[String: Any]] {
                        var parsed: [LiveTestResult] = []
                        for r in results {
                            parsed.append(LiveTestResult(
                                scenario_name: r["scenario_name"] as? String ?? "",
                                scenario_type: r["scenario_type"] as? String ?? "",
                                passed: r["passed"] as? Bool ?? false,
                                score: r["score"] as? Int ?? 0,
                                called_tools: r["called_tools"] as? [String] ?? [],
                                latency_ms: r["latency_ms"] as? Int ?? 0,
                                failures: r["failures"] as? [String] ?? []
                            ))
                        }
                        self.liveTestResults = parsed
                        self.liveTestProgress = (parsed.count, results.count)
                        self.appendLog("Live test complete: \(parsed.filter(\.passed).count)/\(parsed.count) passed")
                    }
                } catch {
                    self.appendLog("Live test parse error: \(error.localizedDescription)")
                }
            }
        }

        liveTestTask = task
        task.resume()
    }

    private func appendLog(_ message: String) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        logs.append("[\(timestamp)] \(message)")
        if logs.count > 200 {
            logs.removeFirst(logs.count - 200)
        }
    }

    deinit {
        liveTestTask?.cancel()
        process?.terminate()
    }
}
