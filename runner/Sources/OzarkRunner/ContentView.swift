import SwiftUI
import AppKit

struct GlassCard: ViewModifier {
    var cornerRadius: CGFloat = 16

    func body(content: Content) -> some View {
        content
            .background(
                .ultraThinMaterial,
                in: RoundedRectangle(cornerRadius: cornerRadius)
            )
            .overlay(
                RoundedRectangle(cornerRadius: cornerRadius)
                    .stroke(
                        LinearGradient(
                            colors: [
                                Color.warmCream.opacity(0.12),
                                Color.warmCream.opacity(0.04),
                                Color.warmCream.opacity(0.08)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 0.75
                    )
            )
            .shadow(color: Color.black.opacity(0.2), radius: 12, y: 4)
    }
}

extension View {
    func glassCard(cornerRadius: CGFloat = 16) -> some View {
        modifier(GlassCard(cornerRadius: cornerRadius))
    }
}

struct ContentView: View {
    @StateObject private var server = ServerManager()

    @State private var selectedAgentURL: URL?
    @State private var agentDisplayName: String = ""
    @State private var agentIsDirectory: Bool = false
    @State private var scenarioCount: Double = 25
    @State private var agentType: String = "customer_support"
    @State private var showLogs: Bool = false
    @State private var loadedAgent: AgentConfig?
    @State private var loadError: String?
    @State private var pulseStart: Bool = false

    @State private var liveTestMode: Bool = false
    @State private var liveEndpoint: String = "http://localhost:8080/agent"
    @State private var liveScenarioCount: Double = 10

    private let agentTypes = [
        "customer_support",
        "code_assistant",
        "data_analysis",
        "autonomous_ops",
    ]

    var body: some View {
        ZStack {
            Color.studioBlack.opacity(0.5)
                .ignoresSafeArea()
                .background(.ultraThinMaterial)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                headerView

                ScrollView(.vertical, showsIndicators: false) {
                    VStack(spacing: 24) {
                        if !liveTestMode {
                            agentPickerCard

                            if let agent = loadedAgent {
                                agentInfoCard(agent)
                                    .transition(.opacity.combined(with: .move(edge: .top)))
                            }

                            configurationCard
                        }

                        liveTestCard

                        if !liveTestMode {
                            serverControlCard
                        }

                        if showLogs {
                            logsCard
                                .transition(.opacity.combined(with: .move(edge: .bottom)))
                        }
                    }
                    .padding(.horizontal, 32)
                    .padding(.top, 32)
                    .padding(.bottom, 40)
                    .frame(maxWidth: 760)
                    .frame(maxWidth: .infinity, alignment: .center)
                }

                footerView
            }
        }
        .animation(.easeOut(duration: 0.3), value: loadedAgent != nil)
        .animation(.easeOut(duration: 0.3), value: showLogs)
        .animation(.easeOut(duration: 0.3), value: liveTestMode)
        .onAppear {
            withAnimation(.easeInOut(duration: 2.0).repeatForever(autoreverses: true)) {
                pulseStart = true
            }
        }
    }

    private var headerView: some View {
        HStack {
            Text("OZARK")
                .font(.system(size: 16, weight: .medium))
                .tracking(2.5)
                .foregroundColor(.warmCream)

            Spacer()

            HStack(spacing: 8) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 8, height: 8)
                    .scaleEffect(server.state.isRunning && pulseStart ? 1.3 : 1.0)
                    .opacity(server.state.isRunning && pulseStart ? 0.6 : 1.0)

                Text(server.isLiveTesting ? "LIVE TEST" : server.state.label)
                    .font(.system(size: 11, weight: .regular))
                    .tracking(1.2)
                    .textCase(.uppercase)
                    .foregroundColor(server.isLiveTesting ? .burntSienna : .greyBrown)
            }
        }
        .padding(.horizontal, 28)
        .padding(.vertical, 16)
        .background(.ultraThinMaterial)
        .overlay(
            Rectangle()
                .frame(height: 0.5)
                .foregroundStyle(
                    LinearGradient(
                        colors: [.warmCream.opacity(0), .warmCream.opacity(0.1), .warmCream.opacity(0)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                ),
            alignment: .bottom
        )
    }

    private var agentPickerCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("AGENT")
                    .font(.system(size: 10, weight: .medium))
                    .tracking(1.8)
                    .foregroundColor(.greyBrown)

                Spacer()

                if selectedAgentURL != nil {
                    Button {
                        clearAgent()
                    } label: {
                        Text("CLEAR")
                            .font(.system(size: 10, weight: .regular))
                            .tracking(1.0)
                            .foregroundColor(.greyBrown)
                    }
                    .buttonStyle(.plain)
                    .onHover { hovering in
                        if hovering {
                            NSCursor.pointingHand.push()
                        } else {
                            NSCursor.pop()
                        }
                    }
                }
            }

            HStack(spacing: 12) {
                Image(systemName: agentIsDirectory ? "folder.fill" : "doc.text.fill")
                    .font(.system(size: 16))
                    .foregroundColor(selectedAgentURL != nil ? .burntSienna : .greyBrown)
                    .frame(width: 24)

                VStack(alignment: .leading, spacing: 2) {
                    if let url = selectedAgentURL {
                        Text(agentDisplayName)
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.warmCream)
                            .lineLimit(1)

                        Text(url.deletingLastPathComponent().path)
                            .font(.system(size: 11))
                            .foregroundColor(.greyBrown)
                            .lineLimit(1)
                            .truncationMode(.head)
                    } else {
                        Text("Select your agent file or folder")
                            .font(.system(size: 14))
                            .foregroundColor(.greyBrown)
                    }
                }

                Spacer()

                Button("Browse") {
                    browseForAgent()
                }
                .buttonStyle(PillGhostButtonStyle())
            }

            if let error = loadError {
                HStack(spacing: 8) {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 11))
                        .foregroundColor(.burntSienna)

                    Text(error)
                        .font(.system(size: 12))
                        .foregroundColor(.burntSienna)
                        .lineLimit(2)
                }
                .padding(.top, 4)
            }
        }
        .padding(24)
        .glassCard()
    }

    private func agentInfoCard(_ agent: AgentConfig) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("LOADED AGENT")
                    .font(.system(size: 10, weight: .medium))
                    .tracking(1.8)
                    .foregroundColor(.greyBrown)

                Spacer()

                Text(agent.framework.uppercased())
                    .font(.system(size: 10, weight: .medium))
                    .tracking(1.0)
                    .foregroundColor(.burntSienna)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 3)
                    .background(.ultraThinMaterial, in: Capsule())
                    .overlay(
                        Capsule()
                            .stroke(Color.burntSienna.opacity(0.5), lineWidth: 0.75)
                    )
            }

            Text(agent.name)
                .font(.system(size: 18, weight: .medium))
                .foregroundColor(.warmCream)

            Text(agent.description)
                .font(.system(size: 13))
                .foregroundColor(.greyBrown)
                .lineSpacing(3)

            HStack(spacing: 0) {
                Text("\(agent.tools.count) tools")
                    .font(.system(size: 12))
                    .foregroundColor(.warmCream)
                    .opacity(0.7)

                Text("  ·  ")
                    .foregroundColor(.corkShadow)

                Text("\(agent.guardrails.count) guardrails")
                    .font(.system(size: 12))
                    .foregroundColor(.warmCream)
                    .opacity(0.7)

                Text("  ·  ")
                    .foregroundColor(.corkShadow)

                Text("\(agent.maxTurns) max turns")
                    .font(.system(size: 12))
                    .foregroundColor(.warmCream)
                    .opacity(0.7)
            }

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    ForEach(agent.tools) { tool in
                        Text(tool.name)
                            .font(.system(size: 11))
                            .foregroundColor(.warmCream)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(.ultraThinMaterial, in: Capsule())
                            .overlay(
                                Capsule()
                                    .stroke(Color.warmCream.opacity(0.1), lineWidth: 0.5)
                            )
                            .opacity(0.68)
                    }
                }
            }
        }
        .padding(24)
        .glassCard()
    }

    private var configurationCard: some View {
        VStack(alignment: .leading, spacing: 20) {
            Text("CONFIGURATION")
                .font(.system(size: 10, weight: .medium))
                .tracking(1.8)
                .foregroundColor(.greyBrown)

            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Scenario Count")
                        .font(.system(size: 13))
                        .foregroundColor(.warmCream)

                    Spacer()

                    Text("\(Int(scenarioCount))")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundColor(.warmCream)
                        .monospacedDigit()
                }

                Slider(value: $scenarioCount, in: 5...200, step: 5)
                    .tint(.burntSienna)

                HStack {
                    Text("5")
                        .font(.system(size: 10))
                        .foregroundColor(.greyBrown)
                    Spacer()
                    Text("200")
                        .font(.system(size: 10))
                        .foregroundColor(.greyBrown)
                }
            }

            Rectangle()
                .frame(height: 0.5)
                .foregroundStyle(
                    LinearGradient(
                        colors: [.corkShadow.opacity(0), .corkShadow, .corkShadow.opacity(0)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )

            VStack(alignment: .leading, spacing: 10) {
                Text("Agent Type")
                    .font(.system(size: 13))
                    .foregroundColor(.warmCream)

                Picker("", selection: $agentType) {
                    ForEach(agentTypes, id: \.self) { type in
                        Text(type.replacingOccurrences(of: "_", with: " ").capitalized)
                            .tag(type)
                    }
                }
                .pickerStyle(.segmented)
                .colorMultiply(.warmCream)
            }
        }
        .padding(24)
        .glassCard()
    }

    private var liveTestCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            HStack {
                Text("LIVE TEST")
                    .font(.system(size: 10, weight: .medium))
                    .tracking(1.8)
                    .foregroundColor(.greyBrown)

                Spacer()

                Toggle("", isOn: $liveTestMode)
                    .toggleStyle(.switch)
                    .tint(.burntSienna)
            }

            if liveTestMode {
                VStack(alignment: .leading, spacing: 14) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Agent Endpoint URL")
                            .font(.system(size: 11))
                            .foregroundColor(.greyBrown)

                        TextField("http://localhost:8080/agent", text: $liveEndpoint)
                            .textFieldStyle(.plain)
                            .font(.system(size: 13, design: .monospaced))
                            .foregroundColor(.warmCream)
                            .padding(10)
                            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.warmCream.opacity(0.08), lineWidth: 0.5)
                            )
                    }

                    HStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Scenarios")
                                .font(.system(size: 11))
                                .foregroundColor(.greyBrown)
                            Text("\(Int(liveScenarioCount))")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(.warmCream)
                        }

                        Slider(value: $liveScenarioCount, in: 5...100, step: 5)
                            .tint(.burntSienna)
                    }

                    Button {
                        server.startLiveTest(
                            endpoint: liveEndpoint,
                            scenarioCount: Int(liveScenarioCount),
                            agentType: agentType
                        )
                    } label: {
                        HStack(spacing: 8) {
                            if server.isLiveTesting {
                                ProgressView()
                                    .progressViewStyle(.circular)
                                    .scaleEffect(0.7)
                                    .tint(.warmCream)
                                Text("Testing...")
                            } else {
                                Image(systemName: "antenna.radiowaves.left.and.right")
                                    .font(.system(size: 10))
                                Text("Run Live Test")
                            }
                        }
                    }
                    .buttonStyle(SiennaFilledButtonStyle())
                    .disabled(server.isLiveTesting || liveEndpoint.isEmpty)

                    if !server.liveTestResults.isEmpty {
                        liveResultsView
                    }
                }
            }
        }
        .padding(24)
        .glassCard()
    }

    private var liveResultsView: some View {
        VStack(alignment: .leading, spacing: 12) {
            Rectangle()
                .frame(height: 0.5)
                .foregroundStyle(
                    LinearGradient(
                        colors: [.corkShadow.opacity(0), .corkShadow, .corkShadow.opacity(0)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )

            HStack {
                Text("RESULTS")
                    .font(.system(size: 10, weight: .medium))
                    .tracking(1.8)
                    .foregroundColor(.greyBrown)
                Spacer()
                let passed = server.liveTestResults.filter(\.passed).count
                let total = server.liveTestResults.count
                Text("\(passed)/\(total) passed")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(passed == total ? .forestGrid : .burntSienna)
            }

            ScrollView(.vertical, showsIndicators: true) {
                LazyVStack(spacing: 6) {
                    ForEach(server.liveTestResults) { result in
                        HStack {
                            Circle()
                                .fill(result.passed ? Color.forestGrid : Color.burntSienna)
                                .frame(width: 6, height: 6)

                            Text(result.scenario_name)
                                .font(.system(size: 12))
                                .foregroundColor(.warmCream)
                                .lineLimit(1)
                                .truncationMode(.middle)

                            Spacer()

                            Text("\(result.score)%")
                                .font(.system(size: 11, weight: .medium, design: .monospaced))
                                .foregroundColor(result.passed ? .forestGrid : .burntSienna)

                            Text("\(result.latency_ms)ms")
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundColor(.greyBrown)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                    }
                }
            }
            .frame(height: 200)
            .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.warmCream.opacity(0.05), lineWidth: 0.5)
            )
        }
    }

    private var serverControlCard: some View {
        VStack(spacing: 20) {
            if server.state.isRunning {
                Button {
                    server.stop()
                } label: {
                    HStack(spacing: 8) {
                        Image(systemName: "stop.fill")
                            .font(.system(size: 10))
                        Text("Stop")
                    }
                }
                .buttonStyle(PillGhostButtonStyle(accentColor: .burntSienna))
            } else if server.state.isStarting {
                HStack(spacing: 10) {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .scaleEffect(0.7)
                        .tint(.warmCream)

                    Text("Starting server…")
                        .font(.system(size: 13))
                        .foregroundColor(.greyBrown)
                }
            } else {
                Button {
                    startServer()
                } label: {
                    HStack(spacing: 10) {
                        Image(systemName: "play.fill")
                            .font(.system(size: 12))
                        Text("Start Simulation")
                    }
                }
                .buttonStyle(SiennaFilledButtonStyle())
                .disabled(server.state.isStarting)
            }

            Button {
                withAnimation { showLogs.toggle() }
            } label: {
                HStack(spacing: 6) {
                    Image(systemName: showLogs ? "chevron.up" : "chevron.down")
                        .font(.system(size: 9))
                    Text(showLogs ? "Hide Logs" : "Show Logs")
                }
            }
            .buttonStyle(PillGhostButtonStyle(accentColor: .greyBrown))
        }
        .frame(maxWidth: .infinity)
        .padding(24)
        .glassCard()
    }

    private var logsCard: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("SERVER LOGS")
                    .font(.system(size: 10, weight: .medium))
                    .tracking(1.8)
                    .foregroundColor(.greyBrown)

                Spacer()

                Text("\(server.logs.count) entries")
                    .font(.system(size: 10))
                    .foregroundColor(.greyBrown)
            }

            ScrollViewReader { proxy in
                ScrollView(.vertical, showsIndicators: true) {
                    LazyVStack(alignment: .leading, spacing: 3) {
                        ForEach(Array(server.logs.enumerated()), id: \.offset) { index, log in
                            Text(log)
                                .font(.system(size: 11, design: .monospaced))
                                .foregroundColor(log.contains("[err]") ? .burntSienna : .greyBrown)
                                .textSelection(.enabled)
                                .id(index)
                        }
                    }
                    .padding(12)
                }
                .frame(height: 160)
                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10))
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.warmCream.opacity(0.05), lineWidth: 0.5)
                )
                .onChange(of: server.logs.count, perform: { _ in
                    if let last = server.logs.indices.last {
                        withAnimation {
                            proxy.scrollTo(last, anchor: .bottom)
                        }
                    }
                })
            }
        }
        .padding(24)
        .glassCard()
    }

    private var footerView: some View {
        HStack {
            Text("v2.1")
                .font(.system(size: 10))
                .foregroundColor(.greyBrown)

            dashedLine

            Text("Local-first")
                .font(.system(size: 10))
                .foregroundColor(.greyBrown)

            dashedLine

            Text("Zero API keys")
                .font(.system(size: 10))
                .foregroundColor(.greyBrown)

            Spacer()

            Text("OZARK AGENT LAB")
                .font(.system(size: 10, weight: .medium))
                .tracking(1.5)
                .foregroundColor(.corkShadow)
        }
        .padding(.horizontal, 28)
        .padding(.vertical, 14)
        .background(.ultraThinMaterial)
        .overlay(
            Rectangle()
                .frame(height: 0.5)
                .foregroundStyle(
                    LinearGradient(
                        colors: [.warmCream.opacity(0), .warmCream.opacity(0.08), .warmCream.opacity(0)],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                ),
            alignment: .top
        )
    }

    private var dashedLine: some View {
        Rectangle()
            .fill(Color.corkShadow)
            .frame(width: 1, height: 10)
            .padding(.horizontal, 8)
    }

    private var statusColor: Color {
        if server.isLiveTesting { return .burntSienna }
        switch server.state {
        case .stopped: return .greyBrown
        case .starting: return .warmCream
        case .running: return .forestGrid
        case .error: return .burntSienna
        }
    }

    private func browseForAgent() {
        let panel = NSOpenPanel()
        panel.title = "Select Agent Configuration"
        panel.message = "Choose a JSON config file or a folder containing one"
        panel.canChooseFiles = true
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        panel.treatsFilePackagesAsDirectories = false
        panel.directoryURL = FileManager.default.homeDirectoryForCurrentUser

        let response = panel.runModal()
        guard response == .OK, let url = panel.url else { return }

        selectedAgentURL = url
        let info = AgentLoader.quickInfo(from: url)
        agentDisplayName = info.name
        agentIsDirectory = info.isDirectory
        loadError = nil

        do {
            let config = try AgentLoader.load(from: url)
            loadedAgent = config
            agentType = config.agentType
            loadError = nil
        } catch {
            loadedAgent = nil
            loadError = error.localizedDescription
        }
    }

    private func clearAgent() {
        selectedAgentURL = nil
        agentDisplayName = ""
        agentIsDirectory = false
        loadedAgent = nil
        loadError = nil
    }

    private func startServer() {
        server.start(
            agentPath: selectedAgentURL,
            scenarioCount: Int(scenarioCount),
            agentType: agentType
        )
    }
}

#Preview {
    ContentView()
        .frame(width: 720, height: 860)
}
