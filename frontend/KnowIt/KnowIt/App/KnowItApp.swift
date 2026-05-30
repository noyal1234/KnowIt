import SwiftUI

@main
struct KnowItApp: App {
    @State private var assembler = AppAssembler()

    var body: some Scene {
        WindowGroup {
            RootView(viewModel: assembler.rootViewModel, assembler: assembler)
        }
    }
}
