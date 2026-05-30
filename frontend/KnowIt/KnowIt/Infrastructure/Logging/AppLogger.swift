import OSLog

nonisolated enum AppLogger {
    private static let subsystem = Bundle.main.bundleIdentifier ?? "com.knowit.KnowIt"

    static let network = Logger(subsystem: subsystem, category: "network")
    static let auth = Logger(subsystem: subsystem, category: "auth")
    static let scan = Logger(subsystem: subsystem, category: "scan")
    static let ocr = Logger(subsystem: subsystem, category: "ocr")
    static let ui = Logger(subsystem: subsystem, category: "ui")
    static let general = Logger(subsystem: subsystem, category: "general")
}
