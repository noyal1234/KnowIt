import Foundation

enum RetryPolicy: Sendable {
    case none
    case exponential(maxAttempts: Int, baseDelay: TimeInterval = 0.5)

    var maxAttempts: Int {
        switch self {
        case .none: return 1
        case .exponential(let max, _): return max
        }
    }

    func delay(forAttempt attempt: Int) -> TimeInterval {
        switch self {
        case .none: return 0
        case .exponential(_, let base):
            return base * pow(2.0, Double(max(0, attempt - 1)))
        }
    }
}
