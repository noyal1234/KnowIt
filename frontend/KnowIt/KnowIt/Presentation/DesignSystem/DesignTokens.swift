import SwiftUI

enum AppColor {
    static let brandPrimary = Color("AccentColor")
    static let textPrimary = Color.primary
    static let textSecondary = Color.secondary
    static let surfaceBackground = Color(.systemGroupedBackground)
    static let surfaceCard = Color(.secondarySystemGroupedBackground)
    static let statusSuccess = Color.green
    static let statusWarning = Color.orange
    static let statusError = Color.red
}

enum AppSpacing {
    static let xs: CGFloat = 4
    static let s: CGFloat = 8
    static let m: CGFloat = 16
    static let l: CGFloat = 24
    static let xl: CGFloat = 32
    static let screenHorizontal: CGFloat = 20
    static let touchTarget: CGFloat = 44
}

enum AppTypography {
    static let headingMedium = Font.title2.weight(.semibold)
    static let body = Font.body
    static let bodySmall = Font.subheadline
    static let caption = Font.caption
}

enum AppRadius {
    static let card: CGFloat = 16
    static let button: CGFloat = 12
}
