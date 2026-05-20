import Foundation
import AppKit
import Combine

// MARK: - Server State

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

// MARK: - Server Manager

@MainActor
class ServerManager: ObservableObject {
    @Published var state: ServerState = .stopped
    @Published var logs: [String] = []

    private var process: Process?
    private var outputPipe: Pipe?
    private var errorPipe: Pipe?

    /// The project root (parent of the `runner/` directory)
    private var projectRoot: URL {
        // The runner binary lives at runner/.build/release/OzarkRunner
        // We need the Ozark project root (parent of runner/)
        let runnerDir = Bundle.main.bundleURL
            .deletingLastPathComponent() // .build/release/
            .deletingLastPathComponent() // .build/
            .deletingLastPathComponent() // runner/

        // If running from Xcode or swift run, try env var or working directory
        if FileManager.default.fileExists(atPath: runnerDir.appendingPathComponent("backend").path) {
            return runnerDir
        }

        // Fallback: look for OZARK_PROJECT_ROOT env var
        if let envRoot = ProcessInfo.processInfo.environment["OZARK_PROJECT_ROOT"] {
            return URL(fileURLWithPath: envRoot)
        }

        // Fallback: current working directory
        return URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
    }

    /// Start the Ozark backend server
    func start(agentPath: URL?, scenarioCount: Int, agentType: String) {
        guard !state.isRunning && !state.isStarting else { return }

        state = .starting
        logs = []
        appendLog("Starting Ozark server...")

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        proc.arguments = ["python3", "-c", "from backend.server import main; main()"]
        proc.currentDirectoryURL = projectRoot

        // Set environment variables
        var env = ProcessInfo.processInfo.environment
        env["PORT"] = "8787"
        if let agentPath = agentPath {
            env["OZARK_AGENT_PATH"] = agentPath.path
        }
        env["OZARK_SCENARIO_COUNT"] = String(scenarioCount)
        env["OZARK_AGENT_TYPE"] = agentType
        proc.environment = env

        // Capture stdout
        let outPipe = Pipe()
        proc.standardOutput = outPipe
        outputPipe = outPipe

        // Capture stderr
        let errPipe = Pipe()
        proc.standardError = errPipe
        errorPipe = errPipe

        // Read output asynchronously
        outPipe.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty, let line = String(data: data, encoding: .utf8) else { return }
            Task { @MainActor [weak self] in
                self?.appendLog(line.trimmingCharacters(in: .whitespacesAndNewlines))
                // Detect successful startup
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

        // Handle termination
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

            // Auto-detect running state after a short delay if we didn't catch the log line
            Task {
                try? await Task.sleep(nanoseconds: 2_500_000_000) // 2.5s
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

    /// Stop the backend server
    func stop() {
        guard let proc = process, proc.isRunning else {
            state = .stopped
            return
        }

        appendLog("Stopping server...")
        proc.terminate()

        // Force kill after 3 seconds if still running
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

    /// Open the browser to the Ozark UI
    func openInBrowser() {
        guard let url = URL(string: "http://127.0.0.1:8787") else { return }
        NSWorkspace.shared.open(url)
    }

    // MARK: - Private

    private func appendLog(_ message: String) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        logs.append("[\(timestamp)] \(message)")
        // Keep log buffer reasonable
        if logs.count > 200 {
            logs.removeFirst(logs.count - 200)
        }
    }

    deinit {
        process?.terminate()
    }
}
