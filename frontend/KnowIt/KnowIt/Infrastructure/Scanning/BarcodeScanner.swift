import AVFoundation

/// Barcode capture via AVFoundation (DataScanner / metadata output — see knowit-scanning.mdc).
struct BarcodeScanner: Sendable {
    func requestPermission() async -> Bool {
        await CameraPermissionProvider().requestAccess()
    }
}
