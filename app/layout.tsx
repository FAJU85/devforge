import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: '⚡ DevForge — AI Coding Agent',
  description: 'Professional AI coding agent with GitHub integration and multi-provider support',
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                document.documentElement.classList.add('dark');
              } else {
                document.documentElement.classList.remove('dark');
              }
            `,
          }}
        />
      </head>
      <body className="bg-white dark:bg-[#0D1116] text-[#0D1116] dark:text-white">
        {children}
      </body>
    </html>
  );
}
