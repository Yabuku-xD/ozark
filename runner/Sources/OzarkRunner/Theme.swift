import SwiftUI

// MARK: - Ozark Design Tokens

extension Color {
    init(hex: UInt, alpha: Double = 1.0) {
        self.init(
            .sRGB,
            red: Double((hex >> 16) & 0xFF) / 255.0,
            green: Double((hex >> 8) & 0xFF) / 255.0,
            blue: Double(hex & 0xFF) / 255.0,
            opacity: alpha
        )
    }

    // Core palette
    static let studioBlack    = Color(hex: 0x100904)
    static let warmCream      = Color(hex: 0xFFEDD7)
    static let corkShadow     = Color(hex: 0x40372E)
    static let darkCork       = Color(hex: 0x382416)
    static let burntSienna    = Color(hex: 0xDC5000)
    static let greyBrown      = Color(hex: 0x6C5F51)
    static let forestGrid     = Color(hex: 0x445231)
}

// MARK: - Ozark Button Styles

struct PillFilledButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .medium))
            .tracking(0.5)
            .textCase(.uppercase)
            .foregroundColor(.warmCream)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)
            .background(Color.darkCork)
            .clipShape(Capsule())
            .opacity(configuration.isPressed ? 0.7 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(.easeOut(duration: 0.18), value: configuration.isPressed)
    }
}

struct PillGhostButtonStyle: ButtonStyle {
    var accentColor: Color = .warmCream

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 13, weight: .regular))
            .tracking(0.5)
            .textCase(.uppercase)
            .foregroundColor(accentColor)
            .padding(.horizontal, 18)
            .padding(.vertical, 9)
            .overlay(
                Capsule()
                    .stroke(accentColor, lineWidth: 1)
            )
            .opacity(configuration.isPressed ? 0.7 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(.easeOut(duration: 0.18), value: configuration.isPressed)
    }
}

struct SiennaFilledButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .semibold))
            .tracking(0.8)
            .textCase(.uppercase)
            .foregroundColor(.warmCream)
            .padding(.horizontal, 32)
            .padding(.vertical, 14)
            .background(Color.burntSienna)
            .clipShape(Capsule())
            .opacity(configuration.isPressed ? 0.8 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.96 : 1.0)
            .animation(.easeOut(duration: 0.18), value: configuration.isPressed)
    }
}
