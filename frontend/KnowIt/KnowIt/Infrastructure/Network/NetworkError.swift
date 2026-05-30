import Foundation

nonisolated enum NetworkError: Error, LocalizedError, Sendable {
    case invalidURL(String)
    case unauthorized
    case forbidden
    case notFound
    case conflict
    case serverError(statusCode: Int)
    case encodingFailed(Error)
    case decodingFailed(Error)
    case cancelled

    var errorDescription: String? {
        switch self {
        case .invalidURL(let path): return "Invalid URL: \(path)"
        case .unauthorized: return "Session expired. Please log in again."
        case .forbidden: return "You do not have permission for this action."
        case .notFound: return "The requested resource was not found."
        case .conflict: return "This action could not be completed."
        case .serverError(let code): return "Server error (\(code)). Please try again."
        case .encodingFailed: return "Failed to encode request."
        case .decodingFailed: return "Failed to read server response."
        case .cancelled: return "Request was cancelled."
        }
    }
}
