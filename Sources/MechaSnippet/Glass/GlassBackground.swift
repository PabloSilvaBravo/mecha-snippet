import SwiftUI

/// Fondo Liquid Glass. Único punto que toca esta API: si se baja el target,
/// solo cambia este archivo (fallback a .ultraThinMaterial).
extension View {
    func glassBackground(cornerRadius: CGFloat = 16) -> some View {
        self.glassEffect(
            .regular,
            in: RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
        )
    }
}
