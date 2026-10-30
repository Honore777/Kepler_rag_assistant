import { Html, Head, Main, NextScript } from 'next/document'

/**
 * Applies the visitor's saved colour theme before first paint so pages never
 * flash the wrong theme on load. Light is the default; dark only if chosen.
 */
const themeBootstrap = `(function(){try{var t=localStorage.getItem('rag-theme');if(t!=='light'&&t!=='dark'){t='light'}document.documentElement.setAttribute('data-theme',t);document.documentElement.style.colorScheme=t}catch(e){document.documentElement.setAttribute('data-theme','light')}})()`

export default function Document() {
  return (
    <Html lang="en" data-theme="light">
      <Head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap"
        />
        <link rel="icon" href="/images/enhanced/logo.png" />
        <script dangerouslySetInnerHTML={{ __html: themeBootstrap }} />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
