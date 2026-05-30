import Foundation

struct AppError: Error, LocalizedError, Equatable, Sendable {
    let message: String
    let isRetryable: Bool

    init(message: String, isRetryable: Bool = true) {
        self.message = message
        self.isRetryable = isRetryable
    }

    var errorDescription: String? { message }

    static func from(_ error: Error) -> AppError {
        if let authError = error as? AuthError {
            return AppError(message: authError.localizedDescription, isRetryable: false)
        }
        if let networkError = error as? NetworkError {
            return AppError(message: networkError.localizedDescription)
        }
        return AppError(message: error.localizedDescription)
    }
}
