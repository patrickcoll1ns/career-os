import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { auth, signOut } from "@/auth";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CareerOS | AI Career Copilot",
  description: "A personalized workspace for career guidance, growth, and reflection.",
};

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const session = await auth();

  return (
    <html
      lang="en"
      data-scroll-behavior="smooth"
      className={`${geistSans.variable} ${geistMono.variable} antialiased`}
    >
      <body>
        {session?.user && (
          <form
            className="fixed right-4 top-4 z-50"
            action={async () => {
              "use server";
              await signOut({ redirectTo: "/signin" });
            }}
          >
            <button
              className="rounded-full border border-[#cbd9d0] bg-white/95 px-4 py-2 text-xs font-semibold text-[#34473c] shadow-sm backdrop-blur hover:bg-[#eef4f0]"
              type="submit"
            >
              Sign out
            </button>
          </form>
        )}
        {children}
      </body>
    </html>
  );
}
