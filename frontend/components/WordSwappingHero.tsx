import Image from 'next/image';
import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/router';

const WordSwappingHero: React.FC = () => {
  const router = useRouter();
  const [currentWordIndex, setCurrentWordIndex] = useState(0);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const heroImages = [
    '/images/kepler-campus-hero.jpg',
    '/images/student-learning.jpg',
    '/images/faculty-teaching.jpg',
    '/images/graduation.jpg',
  ];

  const heroWords = [
    { word: 'Students', description: 'Instant answers for handbooks, policies, and academic support.' },
    { word: 'Staff', description: 'Fast retrieval of operational knowledge and document context.' },
    { word: 'Administration', description: 'Controlled access with secure document governance.' },
    { word: 'Kepler AI', description: 'A campus assistant grounded in the institution’s own data.' },
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.15 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (!isVisible) return;

    const wordTimer = setInterval(() => {
      setCurrentWordIndex((prev) => (prev + 1) % heroWords.length);
    }, 3200);

    const imageTimer = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % heroImages.length);
    }, 4600);

    return () => {
      clearInterval(wordTimer);
      clearInterval(imageTimer);
    };
  }, [isVisible]);

  return (
    <section ref={containerRef} className="relative isolate overflow-hidden">
      <div className="absolute inset-0 bg-rag-dark" />
      <div className="absolute inset-0 bg-rag-grid opacity-30" />
      <div className="absolute inset-0 hero-glow" />
      <div className="absolute -top-20 left-0 h-72 w-72 rounded-full bg-cyan-400/10 blur-3xl animate-drift" />
      <div className="absolute bottom-0 right-0 h-80 w-80 rounded-full bg-emerald-400/10 blur-3xl animate-drift" />

      <div className="container relative grid min-h-screen items-center gap-10 py-24 lg:grid-cols-[1.05fr_0.95fr]">
        <div className={`space-y-8 transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="section-kicker w-fit">
            Option A · Campus knowledge assistant
          </div>

          <div className="space-y-4">
            <div className="relative min-h-[130px] sm:min-h-[150px]">
              {heroWords.map((wordObj, index) => (
                <div
                  key={wordObj.word}
                  className={`absolute inset-0 flex flex-col justify-center transition-all duration-1000 ${
                    index === currentWordIndex && isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6'
                  }`}
                >
                  <h1 className="text-5xl font-semibold tracking-tight text-rag-textPrimary sm:text-6xl lg:text-7xl">
                    {wordObj.word}
                  </h1>
                  <div className="mt-4 max-w-2xl text-lg text-rag-textMuted sm:text-xl">
                    {wordObj.description}
                  </div>
                </div>
              ))}
            </div>

            <p className="max-w-2xl text-base leading-8 text-rag-textMuted sm:text-lg">
              A polished, image-led experience for students, staff, and administrators. The interface uses the dark slate, mint, and cyan palette you specified, with role-aware access and smooth motion throughout.
            </p>
          </div>

          <div className={`flex flex-col gap-4 sm:flex-row ${isVisible ? 'opacity-100' : 'opacity-0'} transition-all duration-1000 delay-300`}>
            <button onClick={() => router.push('/auth/register')} className="rag-button px-8 py-4">
              Student Registration
            </button>
            <button onClick={() => router.push('/auth/login')} className="rag-button-secondary px-8 py-4">
              Login
            </button>
            <button onClick={() => router.push('/chat')} className="rag-button-secondary px-8 py-4">
              Ask the Assistant
            </button>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rag-stat">
              <p className="text-sm text-rag-textMuted">Role-aware</p>
              <p className="mt-1 text-lg font-semibold text-rag-textPrimary">Students to admin</p>
            </div>
            <div className="rag-stat">
              <p className="text-sm text-rag-textMuted">Image-led</p>
              <p className="mt-1 text-lg font-semibold text-rag-textPrimary">Campus storytelling</p>
            </div>
            <div className="rag-stat">
              <p className="text-sm text-rag-textMuted">Motion</p>
              <p className="mt-1 text-lg font-semibold text-rag-textPrimary">Soft reveals + float</p>
            </div>
          </div>
        </div>

        <div className={`relative transition-all duration-1000 delay-200 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <div className="absolute -inset-6 rounded-[2rem] bg-cyan-400/10 blur-3xl" />
          <div className="glass-panel relative overflow-hidden p-4">
            <div className="relative overflow-hidden rounded-[1.6rem] border border-white/10 bg-rag-surface min-h-[420px] shadow-glow">
              <Image
                src={heroImages[currentImageIndex]}
                alt="Kepler College campus"
                fill
                priority
                className="object-cover transition-opacity duration-1000"
              />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/35 to-transparent" />
              <div className="absolute left-5 top-5 rounded-full border border-white/10 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-rag-textPrimary backdrop-blur-xl">
                Live campus view
              </div>
              <div className="absolute bottom-5 left-5 right-5 grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/10 bg-black/35 p-4 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.2em] text-cyan-400">Access</p>
                  <p className="mt-1 text-sm text-rag-textPrimary">Secure, role-based entry</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/35 p-4 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.2em] text-cyan-400">Answers</p>
                  <p className="mt-1 text-sm text-rag-textPrimary">Grounded in internal docs</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-black/35 p-4 backdrop-blur-xl">
                  <p className="text-xs uppercase tracking-[0.2em] text-cyan-400">Style</p>
                  <p className="mt-1 text-sm text-rag-textPrimary">Dark, modern, polished</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            {heroImages.slice(1, 4).map((image, index) => (
              <div key={image} className="glass-panel relative h-28 overflow-hidden rounded-2xl border border-white/10">
                <Image src={image} alt={`Kepler campus ${index + 1}`} fill className="object-cover" />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 to-transparent" />
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={`absolute bottom-6 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2 text-rag-textMuted transition-opacity duration-1000 ${isVisible ? 'opacity-100' : 'opacity-0'}`}>
        <div className="h-6 w-px bg-white/40" />
        <svg className="h-6 w-6 animate-bounce text-rag-textPrimary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
      </div>
    </section>
  );
};

export default WordSwappingHero;
