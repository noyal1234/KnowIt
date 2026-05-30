import Vision

/// On-device label OCR via Apple Vision (preferred over server OCR).
struct VisionTextRecognizer: Sendable {
    func recognizeText(from imageData: Data) async throws -> String {
        // TODO: Implement VNRecognizeTextRequest pipeline (knowit-scanning.mdc)
        throw ScanError.ocrFailed
    }
}

enum ScanError: Error, LocalizedError, Sendable {
    case ocrFailed
    case cameraPermissionDenied

    var errorDescription: String? {
        switch self {
        case .ocrFailed: return "Could not read text from the label."
        case .cameraPermissionDenied: return "Camera access is required to scan products."
        }
    }
}
