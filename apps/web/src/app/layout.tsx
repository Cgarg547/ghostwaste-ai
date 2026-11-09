import './style.css';
import './design-system.css';
export const metadata = { title: 'GhostWaste AI', description: 'Predict tomorrow’s waste. Prevent it today.' };
export const viewport = { width: 'device-width', initialScale: 1 };
export default function RootLayout({children}:{children:React.ReactNode}) {return <html lang="en" data-scroll-behavior="smooth"><body>{children}</body></html>}
