import type { Metadata, Viewport } from "next";
import { cookies } from "next/headers";
import { Poppins, Readex_Pro } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/context/LanguageContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { LANGUAGE_COOKIE, type Language } from "@/lib/languageCookie";
import { THEME_COOKIE, parseThemePreference } from "@/lib/themeCookie";
import { MotionProvider } from "@/components/providers/MotionProvider";
import { AssistantBubbleProvider } from "@/components/customer/AssistantBubbleProvider";
import { GlobalDialogProvider } from "@/components/common/GlobalDialogProvider";
import { VisitStatus } from "@/components/customer/VisitStatus";

// Interface text: Readex Pro, a clean modern Arabic/Latin sans, very legible at small sizes.
const readex = Readex_Pro({
  subsets: ["arabic", "latin"],
  variable: "--font-readex",
  display: "swap",
});

// Headlines and prices: Poppins, the heading face of Pino Yard's own website; Arabic falls back to Readex Pro.
const poppins = Poppins({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-poppins",
  display: "swap",
});

// The browser tab title and description follow the visitor's language too.
export async function generateMetadata(): Promise<Metadata> {
  const english = (await cookies()).get(LANGUAGE_COOKIE)?.value === "en";
  return english
    ? {
        title: "Pino Yard | بينو يارد — Pine & dine, an experience by design",
        icons: { apple: "/brand/apple-touch-icon.png" },
        description: "Pino Yard Restaurant & Cafe in Amman: international cuisine, specialty coffee and shisha, ordered from your table",
      }
    : {
        title: "بينو يارد | Pino Yard — مطعم وكافيه",
        icons: { apple: "/brand/apple-touch-icon.png" },
        description: "مطعم وكافيه بينو يارد في عمّان: مطبخ عالمي وقهوة مختصة وأراجيل، اطلب من طاولتك",
      };
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
  // The on-screen keyboard shrinks the page instead of covering the chat box (Android).
  interactiveWidget: "resizes-content",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f6f5f1" },
    { media: "(prefers-color-scheme: dark)", color: "#0b0f17" },
  ],
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const store = await cookies();
  // The guest's language and theme come with the request, so the first page is already right.
  const lang: Language = store.get(LANGUAGE_COOKIE)?.value === "en" ? "en" : "ar";
  const theme = parseThemePreference(store.get(THEME_COOKIE)?.value);
  return (
    <html
      lang={lang}
      dir={lang === "ar" ? "rtl" : "ltr"}
      data-theme={theme === "system" ? undefined : theme}
      className={`${readex.variable} ${poppins.variable} h-full`}
      data-scroll-behavior="smooth"
      suppressHydrationWarning
    >
      <body
        className="min-h-full min-h-dvh flex flex-col antialiased overflow-x-hidden"
        suppressHydrationWarning
      >
        <ThemeProvider initialPreference={theme}>
          <LanguageProvider initialLang={lang}>
            <MotionProvider>
              <GlobalDialogProvider>
                <AssistantBubbleProvider>{children}</AssistantBubbleProvider>
                <VisitStatus />
              </GlobalDialogProvider>
            </MotionProvider>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
