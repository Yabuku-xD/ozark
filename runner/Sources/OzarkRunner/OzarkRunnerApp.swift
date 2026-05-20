import SwiftUI

@main
struct OzarkRunnerApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
                .frame(minWidth: 680, minHeight: 780)
        }
        .windowStyle(.hiddenTitleBar)
        .defaultSize(width: 720, height: 860)
    }
}

// MARK: - App Delegate

class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationWillFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular)
    }

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Bring app to front above all other windows
        NSApplication.shared.activate(ignoringOtherApps: true)

        // Set the app icon for the Dock
        if let root = ProcessInfo.processInfo.environment["OZARK_PROJECT_ROOT"],
           let icon = NSImage(contentsOfFile: "\(root)/assets/logo.png") {
            NSApplication.shared.applicationIconImage = icon
        }

        // Style the window for liquid glass
        if let window = NSApplication.shared.windows.first {
            window.titlebarAppearsTransparent = true
            window.isOpaque = false
            window.backgroundColor = NSColor(red: 16/255.0, green: 9/255.0, blue: 4/255.0, alpha: 0.78)

            // Center the window on screen
            window.center()

            // Ensure it's the key and main window
            window.makeKeyAndOrderFront(nil)
            window.orderFrontRegardless()
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }
}
