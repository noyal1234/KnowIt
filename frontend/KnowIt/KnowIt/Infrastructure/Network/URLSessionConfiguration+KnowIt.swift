import Foundation

extension URLSessionConfiguration {
    static var knowItDefault: URLSessionConfiguration {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 120
        config.waitsForConnectivity = true
        config.httpAdditionalHeaders = ["X-Client": "iOS-KnowIt"]
        return config
    }
}
