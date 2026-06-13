const esbuild = require("esbuild");

const isWatch = process.argv.includes("--watch");
const isProduction = process.env.NODE_ENV === "production";

const config = {
  entryPoints: ["src/index.ts"],
  bundle: true,
  outfile: "dist/bundle.js",
  format: "esm",
  platform: "browser",
  target: ["ES2020"],
  sourcemap: !isProduction,
  minify: isProduction,
  loader: {
    ".css": "text",
  },
  define: {
    "process.env.NODE_ENV": isProduction ? '"production"' : '"development"',
  },
};

if (isWatch) {
  esbuild
    .context(config)
    .then((ctx) => {
      console.log("👀 Watching for changes...");
      return ctx.watch();
    })
    .catch(() => process.exit(1));
} else {
  esbuild.build(config).catch(() => process.exit(1));
}
