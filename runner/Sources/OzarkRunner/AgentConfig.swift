import Foundation

// MARK: - Agent Configuration Model

/// Represents a user's agent configuration loaded from a JSON file.
/// Matches the schema used by the Ozark backend.
struct AgentConfig: Codable, Identifiable {
    var id: String
    var name: String
    var description: String
    var agentType: String
    var framework: String
    var systemPrompt: String
    var tools: [ToolDef]
    var guardrails: [GuardrailDef]
    var maxTurns: Int
    var model: String

    enum CodingKeys: String, CodingKey {
        case id, name, description, framework, tools, guardrails, model
        case agentType = "agent_type"
        case systemPrompt = "system_prompt"
        case maxTurns = "max_turns"
    }

    struct ToolDef: Codable, Identifiable {
        var id: String { name }
        var name: String
        var description: String
        var risk: String
        var requiresConfirmation: Bool?

        enum CodingKeys: String, CodingKey {
            case name, description, risk
            case requiresConfirmation = "requires_confirmation"
        }
    }

    struct GuardrailDef: Codable, Identifiable {
        var id: String
        var rule: String
        var severity: String
        var category: String
    }
}

// MARK: - Agent File Loader

enum AgentLoadError: LocalizedError {
    case fileNotFound(String)
    case invalidJSON(String)
    case missingRequiredFields(String)
    case directoryNoConfig(String)

    var errorDescription: String? {
        switch self {
        case .fileNotFound(let path):
            return "File not found: \(path)"
        case .invalidJSON(let detail):
            return "Invalid JSON: \(detail)"
        case .missingRequiredFields(let detail):
            return "Missing required fields: \(detail)"
        case .directoryNoConfig(let path):
            return "No agent config found in: \(path)"
        }
    }
}

struct AgentLoader {
    /// Load an agent config from a file or directory.
    /// If given a directory, looks for config.json, agent.json, or ozark.json inside it.
    static func load(from url: URL) throws -> AgentConfig {
        var targetURL = url

        if url.hasDirectoryPath || (try? url.resourceValues(forKeys: [.isDirectoryKey]))?.isDirectory == true {
            // Search for known config filenames in the directory
            let candidates = ["config.json", "agent.json", "ozark.json", "agent_config.json"]
            var found = false
            for candidate in candidates {
                let candidateURL = url.appendingPathComponent(candidate)
                if FileManager.default.fileExists(atPath: candidateURL.path) {
                    targetURL = candidateURL
                    found = true
                    break
                }
            }
            if !found {
                // Try to find any .json file
                let contents = try FileManager.default.contentsOfDirectory(at: url, includingPropertiesForKeys: nil)
                if let firstJSON = contents.first(where: { $0.pathExtension == "json" }) {
                    targetURL = firstJSON
                } else {
                    throw AgentLoadError.directoryNoConfig(url.path)
                }
            }
        }

        guard FileManager.default.fileExists(atPath: targetURL.path) else {
            throw AgentLoadError.fileNotFound(targetURL.path)
        }

        let data = try Data(contentsOf: targetURL)

        // First try to decode as a full agent config
        do {
            var config = try JSONDecoder().decode(AgentConfig.self, from: data)
            if config.id.isEmpty {
                config.id = config.name.lowercased().replacingOccurrences(of: " ", with: "-") + "-" + UUID().uuidString.prefix(6).lowercased()
            }
            return config
        } catch {
            // Try to decode as a nested format: { "config": { ... } }
            if let wrapper = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let configDict = wrapper["config"] as? [String: Any] {
                let configData = try JSONSerialization.data(withJSONObject: configDict)
                var config = try JSONDecoder().decode(AgentConfig.self, from: configData)
                if config.id.isEmpty {
                    config.id = config.name.lowercased().replacingOccurrences(of: " ", with: "-") + "-" + UUID().uuidString.prefix(6).lowercased()
                }
                return config
            }
            throw AgentLoadError.invalidJSON(error.localizedDescription)
        }
    }

    /// Get display info from a URL without fully parsing
    static func quickInfo(from url: URL) -> (name: String, isDirectory: Bool) {
        let isDir = (try? url.resourceValues(forKeys: [.isDirectoryKey]))?.isDirectory ?? false
        let name = url.lastPathComponent
        return (name, isDir)
    }
}
