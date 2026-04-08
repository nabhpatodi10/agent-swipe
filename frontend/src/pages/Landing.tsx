import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Zap, Compass, Heart, ArrowRight, Sparkles } from "lucide-react";
import { Button } from "../components/ui/Button";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: "easeOut" as const } },
};

const stagger = {
  visible: { transition: { staggerChildren: 0.15 } },
};

const features = [
  {
    icon: Compass,
    title: "Discover",
    description:
      "Browse a curated marketplace of AI agents built for every use case imaginable.",
  },
  {
    icon: Heart,
    title: "Match",
    description:
      "Swipe through agents and find the perfect match for your workflow in seconds.",
  },
  {
    icon: Zap,
    title: "Deploy",
    description:
      "Integrate matched agents into your stack with one click and start automating.",
  },
];

const steps = [
  { num: "01", title: "Create an account", desc: "Sign up in seconds and tell us what you need." },
  { num: "02", title: "Swipe & discover", desc: "Browse agents tailored to your interests and goals." },
  { num: "03", title: "Start building", desc: "Deploy agents and supercharge your productivity." },
];

export function Landing() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-surface-0 grid-bg">
      {/* Ambient glow orbs */}
      <div className="pointer-events-none absolute -top-40 -left-40 h-[500px] w-[500px] rounded-full bg-accent/20 blur-[160px]" />
      <div className="pointer-events-none absolute top-1/3 -right-32 h-[400px] w-[400px] rounded-full bg-brown/15 blur-[140px]" />
      <div className="pointer-events-none absolute bottom-0 left-1/2 h-[350px] w-[350px] -translate-x-1/2 rounded-full bg-accent/10 blur-[120px]" />

      {/* Navbar */}
      <nav className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
        <Link to="/" className="flex items-center gap-2">
          <Zap className="h-7 w-7 text-accent" />
          <span className="text-xl font-bold gradient-text">AgentSwipe</span>
        </Link>
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Login</Button>
          </Link>
          <Link to="/register">
            <Button size="sm">Register</Button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-5xl px-6 pt-20 pb-32 text-center">
        <motion.div variants={stagger} initial="hidden" animate="visible">
          <motion.div variants={fadeUp} className="mb-6 inline-flex items-center gap-2 rounded-full border border-brown-light/20 bg-brown/5 px-4 py-1.5 text-sm text-text-secondary">
            <Sparkles className="h-4 w-4 text-brown" />
            The AI Agent Marketplace
          </motion.div>

          <motion.h1
            variants={fadeUp}
            className="text-5xl font-extrabold leading-tight tracking-tight sm:text-6xl lg:text-7xl"
          >
            <span className="gradient-text">Discover AI Agents</span>
            <br />
            <span className="text-text-primary">That Work For You</span>
          </motion.h1>

          <motion.p
            variants={fadeUp}
            className="mx-auto mt-6 max-w-2xl text-lg text-text-secondary"
          >
            Swipe through a curated marketplace of intelligent agents. Find your
            perfect match, deploy in one click, and let AI handle the rest.
          </motion.p>

          <motion.div variants={fadeUp} className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link to="/register">
              <Button size="lg" className="glow-md">
                Get Started <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg">Sign In</Button>
            </Link>
          </motion.div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 pb-28">
        <motion.div
          variants={stagger}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          className="grid gap-6 sm:grid-cols-3"
        >
          {features.map((f) => (
            <motion.div key={f.title} variants={fadeUp} className="glass glass-hover rounded-2xl p-8 text-center">
              <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-accent/15">
                <f.icon className="h-7 w-7 text-accent" />
              </div>
              <h3 className="text-xl font-semibold text-text-primary">{f.title}</h3>
              <p className="mt-2 text-text-muted">{f.description}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* How it works */}
      <section className="relative z-10 mx-auto max-w-5xl px-6 pb-32">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          variants={stagger}
        >
          <motion.h2 variants={fadeUp} className="mb-14 text-center text-3xl font-bold text-text-primary sm:text-4xl">
            How It <span className="gradient-text">Works</span>
          </motion.h2>

          <div className="grid gap-10 sm:grid-cols-3">
            {steps.map((s) => (
              <motion.div key={s.num} variants={fadeUp} className="relative text-center">
                <span className="text-5xl font-extrabold text-accent/20">{s.num}</span>
                <h3 className="mt-2 text-lg font-semibold text-text-primary">{s.title}</h3>
                <p className="mt-1 text-text-muted">{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>
    </div>
  );
}
