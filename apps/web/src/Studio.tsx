import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  BookOpen,
  Check,
  ChevronRight,
  Clock3,
  Download,
  Film,
  Layers3,
  LoaderCircle,
  LogOut,
  Menu,
  Play,
  Plus,
  RotateCcw,
  Save,
  Sparkles,
  Square,
  Volume2,
  WandSparkles,
  X,
} from "lucide-react";
import { api, post } from "./api";
import { Brand } from "./AuthScreen";
import {
  busy,
  type Project,
  type SceneSpec,
  type Storyboard,
  type User,
} from "./types";

const labels: Record<string, string> = {
  concept: "Concept diagram",
  graph: "Function graph",
  steps: "Step by step",
  comparison: "Side by side",
  number_line: "Number array",
  geometry: "Geometric proof",
};
const statusLabels: Record<string, string> = {
  draft: "Ready to review",
  completed: "Video ready",
  queued: "Queued",
  planning: "Planning",
  narrating: "Narrating",
  rendering: "Animating",
  assembling: "Finishing",
  failed: "Needs attention",
  cancelled: "Cancelled",
};
const samples = [
  "Why does a parabola curve?",
  "How does binary search work?",
  "Explain Newton’s first law",
];
const getSelected = () =>
  new URLSearchParams(window.location.search).get("project");
const clone = <T,>(value: T): T => JSON.parse(JSON.stringify(value));

function SceneSketch({
  scene,
  number = 1,
}: {
  scene?: SceneSpec;
  number?: number;
}) {
  return (
    <div className={`scene-sketch ${scene?.kind ?? "welcome-sketch"}`}>
      <div className="sketch-top">
        <span>VIZION / VISUAL NOTES</span>
        <span>SCENE {String(number).padStart(2, "0")}</span>
      </div>
      <h3>{scene?.title ?? "A simple rule. A whole new shape."}</h3>
      {!scene ? (
        <svg
          className="parabola"
          viewBox="0 0 600 280"
          aria-label="Example parabola illustration"
        >
          <defs>
            <pattern
              id="previewGrid"
              width="35"
              height="35"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M35 0H0V35"
                fill="none"
                stroke="#263329"
                strokeWidth=".75"
              />
            </pattern>
          </defs>
          <rect
            x="25"
            y="10"
            width="550"
            height="245"
            fill="url(#previewGrid)"
          />
          <path d="M35 225H565 M300 250V20" stroke="#657468" />
          <path
            d="M120 25 Q300 425 480 25"
            stroke="#d2f48c"
            strokeWidth="3"
            fill="none"
          />
          <circle cx="370" cy="125" r="5" fill="#d2f48c" />
          <text x="390" y="202" fill="#e6eddf" fontSize="32" fontFamily="serif">
            y = x²
          </text>
        </svg>
      ) : (
        <div className="sketch-content">
          {scene.kind === "graph" ? (
            <div className="equation-hero">
              {scene.equation || `f(x) = ${scene.expression}`}
              <span>
                Function graph · {scene.x_min} ≤ x ≤ {scene.x_max}
              </span>
            </div>
          ) : scene.kind === "number_line" ? (
            <div className="sketch-array">
              {scene.values.map((value, index) => (
                <span
                  key={index}
                  className={index === scene.highlight_index ? "highlight" : ""}
                >
                  {value}
                  <small>{index}</small>
                </span>
              ))}
            </div>
          ) : scene.kind === "geometry" ? (
            <div className="triangle-sketch">
              <svg viewBox="0 0 240 140" aria-hidden="true">
                <path
                  d="M50 110H195L50 20Z"
                  fill="#cbf47718"
                  stroke="#cbf477"
                  strokeWidth="2"
                />
                <path d="M50 92H68V110" stroke="#84917f" fill="none" />
              </svg>
              <span>{scene.equation || "a² + b² = c²"}</span>
            </div>
          ) : (
            <div
              className={`sketch-nodes ${scene.kind === "steps" ? "vertical" : ""}`}
            >
              {scene.labels.slice(0, 5).map((text, index) => (
                <div key={index}>
                  <span>
                    {scene.kind === "steps" && <b>{index + 1}</b>}
                    {text}
                  </span>
                  {index < scene.labels.length - 1 &&
                    scene.kind === "concept" && <ArrowRight size={18} />}
                </div>
              ))}
            </div>
          )}
          {!!scene.equation && !["graph", "geometry"].includes(scene.kind) && (
            <div className="sketch-equation">{scene.equation}</div>
          )}
        </div>
      )}
      <div className="sketch-bottom">
        <span>
          {scene ? "STORYBOARD SKETCH" : "EXAMPLE / THE SHAPE OF SQUARING"}
        </span>
        <span>
          <Volume2 size={12} /> Narrated animation
        </span>
      </div>
    </div>
  );
}

export function Studio({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<string | null>(getSelected);
  const [project, setProject] = useState<Project | null>(null);
  const [draft, setDraft] = useState<Storyboard | null>(null);
  const [dirty, setDirty] = useState(false);
  const [sceneIndex, setSceneIndex] = useState(0);
  const [topic, setTopic] = useState("");
  const [audience, setAudience] = useState("beginner");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [sidebar, setSidebar] = useState(false);
  const [editorTab, setEditorTab] = useState<"narration" | "visuals">(
    "narration",
  );
  const activeProject = useRef<string | null>(selected);
  const draftDirty = useRef(false);
  const createIntent = useRef<{ body: string; key: string } | null>(null);
  activeProject.current = selected;
  draftDirty.current = dirty;
  const selectedStatus = project?.status;

  const refreshList = useCallback(async () => {
    setProjects(await api<Project[]>("/projects"));
  }, []);
  useEffect(() => {
    refreshList().catch((err) => setError(err.message));
    const timer = window.setInterval(() => {
      refreshList().catch(() => {});
    }, 6000);
    const onPopState = () => {
      setDirty(false);
      setSelected(getSelected());
    };
    window.addEventListener("popstate", onPopState);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("popstate", onPopState);
    };
  }, [refreshList]);

  useEffect(() => {
    if (!selected) {
      setProject(null);
      setDraft(null);
      return;
    }
    const controller = new AbortController();
    let timer: number | undefined;
    const load = async () => {
      try {
        const value = await api<Project>(
          `/projects/${encodeURIComponent(selected)}`,
          { signal: controller.signal },
        );
        if (controller.signal.aborted || activeProject.current !== selected)
          return;
        setProject(value);
        if (!draftDirty.current)
          setDraft(value.storyboard ? clone(value.storyboard) : null);
        if (busy(value)) timer = window.setTimeout(load, 2000);
      } catch (err) {
        if (!controller.signal.aborted)
          setError(
            err instanceof Error ? err.message : "Could not load this project.",
          );
      }
    };
    load();
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [selected, selectedStatus]);

  function choose(id: string | null) {
    if (
      dirty &&
      !window.confirm("Leave without saving your storyboard changes?")
    )
      return;
    setDirty(false);
    draftDirty.current = false;
    setProject(null);
    setDraft(null);
    setSceneIndex(0);
    setError("");
    setSelected(id);
    setSidebar(false);
    const query = id ? `?project=${encodeURIComponent(id)}` : "/";
    window.history.pushState({}, "", query);
  }

  async function create(example = false) {
    if (pending) return;
    setPending(true);
    setError("");
    try {
      const body = {
        topic: example ? "Why a parabola curves" : topic,
        audience,
        example,
      };
      const signature = JSON.stringify(body);
      if (createIntent.current?.body !== signature)
        createIntent.current = { body: signature, key: crypto.randomUUID() };
      const value = await post<Project>("/projects", body, {
        "Idempotency-Key": createIntent.current.key,
      });
      createIntent.current = null;
      choose(value.id);
      setProject(value);
      await refreshList();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not create the lesson.",
      );
    } finally {
      setPending(false);
    }
  }

  async function action(name: "render" | "save" | "retry" | "cancel") {
    if (!project || pending) return;
    setPending(true);
    setError("");
    try {
      let current = project;
      if (dirty && draft && ["save", "render"].includes(name)) {
        current = await api<Project>(`/projects/${project.id}/storyboard`, {
          method: "PUT",
          body: JSON.stringify({
            storyboard: draft,
            revision: project.revision,
          }),
        });
        if (activeProject.current === current.id) {
          setDirty(false);
          draftDirty.current = false;
          setDraft(current.storyboard ? clone(current.storyboard) : null);
        }
      }
      if (name !== "save")
        current = await post<Project>(
          `/projects/${project.id}/${name}`,
          name === "render" ? { revision: current.revision } : undefined,
        );
      if (activeProject.current === current.id) setProject(current);
      await refreshList();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "This action could not be completed.",
      );
    } finally {
      setPending(false);
    }
  }

  function editScene(update: Partial<SceneSpec>) {
    if (!draft) return;
    setDraft({
      ...draft,
      scenes: draft.scenes.map((scene, index) =>
        index === sceneIndex ? { ...scene, ...update } : scene,
      ),
    });
    setDirty(true);
  }

  function moveScene(direction: number) {
    if (!draft) return;
    const scenes = [...draft.scenes],
      next = sceneIndex + direction;
    if (next < 0 || next >= scenes.length) return;
    [scenes[next], scenes[sceneIndex]] = [scenes[sceneIndex], scenes[next]];
    setDraft({ ...draft, scenes });
    setSceneIndex(next);
    setDirty(true);
  }

  const currentScene = draft?.scenes[sceneIndex];
  const isBusy = busy(project);
  const wordCount =
    draft?.scenes.reduce(
      (sum, scene) => sum + scene.narration.trim().split(/\s+/).length,
      0,
    ) ?? 0;

  return (
    <div className="studio">
      {sidebar && (
        <button
          className="sidebar-scrim"
          aria-label="Close project navigation"
          onClick={() => setSidebar(false)}
        />
      )}
      <aside className={`sidebar ${sidebar ? "open" : ""}`}>
        <button
          className="brand-button"
          onClick={() => choose(null)}
          aria-label="Vizion home"
        >
          <Brand />
        </button>
        <button className="button new-project" onClick={() => choose(null)}>
          <Plus size={17} /> New lesson <span>↗</span>
        </button>
        <div className="nav-heading">
          <span>YOUR WORKSPACE</span>
          <span>{projects.length.toString().padStart(2, "0")}</span>
        </div>
        <div className="project-navigation" aria-label="Your projects">
          {!projects.length && (
            <p className="empty-projects">
              Your first lesson belongs here.
              <br />
              Start with something you’re curious about.
            </p>
          )}
          {projects.map((item) => (
            <button
              key={item.id}
              className={`project-link ${selected === item.id ? "selected" : ""}`}
              onClick={() => choose(item.id)}
            >
              <span className={`project-icon ${item.status}`}>
                <Film size={16} />
              </span>
              <span>
                <strong>{item.title}</strong>
                <small>{statusLabels[item.status]}</small>
              </span>
              {busy(item) && <LoaderCircle size={13} className="spin" />}
            </button>
          ))}
        </div>
        <div className="sidebar-note">
          <div className="note-icon">
            <BookOpen size={17} />
          </div>
          <strong>A good explanation starts small.</strong>
          <p>
            One idea. A concrete example.
            <br />A moment that makes it click.
          </p>
        </div>
        <div className="account">
          <span className="avatar">{user.email.slice(0, 1).toUpperCase()}</span>
          <span>
            <strong>My workspace</strong>
            <small>{user.email}</small>
          </span>
          <button
            className="icon-button"
            title="Sign out"
            aria-label="Sign out"
            onClick={async () => {
              try {
                await post("/auth/logout");
                onLogout();
              } catch (err) {
                setError(
                  err instanceof Error ? err.message : "Could not sign out.",
                );
              }
            }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>
      <div className="studio-main">
        <header className="topbar">
          <div>
            <button
              className="icon-button mobile-menu"
              aria-label="Open project navigation"
              onClick={() => setSidebar(true)}
            >
              <Menu size={20} />
            </button>
            <span className="breadcrumb">Workspace</span>
            <ChevronRight size={14} />
            <span>{selected ? "Lesson studio" : "Overview"}</span>
          </div>
          <span className="workspace-badge">
            <span className="live-dot" /> PERSONAL WORKSPACE
          </span>
        </header>
        {error && (
          <div className="global-error" role="alert">
            {error}
            <button
              className="icon-button"
              aria-label="Dismiss error"
              onClick={() => setError("")}
            >
              <X size={16} />
            </button>
          </div>
        )}
        {!selected ? (
          <div className="home-scroll">
            <div className="home-content">
              <div className="home-intro">
                <span className="eyebrow">
                  <Sparkles size={14} /> A LITTLE CURIOSITY GOES A LONG WAY
                </span>
                <h1>
                  What will you
                  <br />
                  <em>make clear</em> today?
                </h1>
                <p>
                  Give an idea a voice, a shape, and a story worth watching.
                </p>
              </div>
              <div className="creation-grid">
                <form
                  className="topic-card"
                  onSubmit={(event: FormEvent) => {
                    event.preventDefault();
                    create();
                  }}
                >
                  <div className="card-label">
                    <span>01 / START WITH AN IDEA</span>
                    <WandSparkles size={17} />
                  </div>
                  <label className="sr-only" htmlFor="topic">
                    What topic would you like to explain?
                  </label>
                  <textarea
                    id="topic"
                    placeholder="Explain a concept, ask a question, or describe something you’d love to teach…"
                    value={topic}
                    onChange={(event) => setTopic(event.target.value)}
                    minLength={8}
                    maxLength={1500}
                    required
                  />
                  <div className="topic-hints">
                    <span>Be specific. One concept works beautifully.</span>
                    <span>{topic.length}/1500</span>
                  </div>
                  <div className="topic-settings">
                    <label>
                      <span>MADE FOR</span>
                      <select
                        aria-label="Lesson audience"
                        value={audience}
                        onChange={(event) => setAudience(event.target.value)}
                      >
                        <option value="beginner">Curious beginners</option>
                        <option value="intermediate">
                          Intermediate learners
                        </option>
                      </select>
                    </label>
                    <span>
                      <Clock3 size={15} /> A short explainer
                    </span>
                  </div>
                  <button
                    className="button primary wide"
                    disabled={pending || topic.trim().length < 8}
                  >
                    {pending ? (
                      <LoaderCircle size={17} className="spin" />
                    ) : (
                      <Sparkles size={17} />
                    )}{" "}
                    Create storyboard <ArrowRight size={17} />
                  </button>
                  <p className="form-footnote">
                    Review the story first. Render when it feels right.
                  </p>
                </form>
                <div className="example-card">
                  <SceneSketch />
                  <div className="example-card-footer">
                    <span>
                      <strong>See an idea take shape.</strong>
                      <small>
                        A ready-to-render example, no prompt needed.
                      </small>
                    </span>
                    <button
                      className="circle-button"
                      disabled={pending}
                      onClick={() => create(true)}
                      aria-label="Try the parabola example"
                    >
                      <ArrowUp
                        size={19}
                        style={{ transform: "rotate(45deg)" }}
                      />
                    </button>
                  </div>
                </div>
              </div>
              <div className="sample-topics">
                <span>NEED A SPARK?</span>
                {samples.map((sample) => (
                  <button
                    key={sample}
                    onClick={() => {
                      setTopic(sample);
                      document.getElementById("topic")?.focus();
                    }}
                  >
                    {sample}
                    <ArrowRight size={13} />
                  </button>
                ))}
              </div>
              <div className="how-it-works">
                <div>
                  <span>01</span>
                  <strong>Find the story</strong>
                  <p>We turn your topic into a short, focused storyboard.</p>
                </div>
                <div>
                  <span>02</span>
                  <strong>Make it yours</strong>
                  <p>Refine the words, labels, and order of each scene.</p>
                </div>
                <div>
                  <span>03</span>
                  <strong>Bring it to life</strong>
                  <p>Render a narrated animation, then download and share.</p>
                </div>
              </div>
            </div>
            <footer className="workspace-footer">
              <span>Made for understanding.</span>
              <span>Animated lessons · Real curiosity</span>
            </footer>
          </div>
        ) : !project ? (
          <div className="boot">
            <LoaderCircle className="spin" />
            <p>Opening lesson…</p>
          </div>
        ) : (
          <div className="lesson-scroll">
            <div className="lesson-heading">
              <div>
                <button
                  className="text-button back-link"
                  onClick={() => choose(null)}
                >
                  <ArrowLeft size={13} /> All lessons
                </button>
                <h1>{project.title}</h1>
                <p>{project.storyboard?.objective || project.topic}</p>
              </div>
              <div className="lesson-actions">
                <span className={`status-pill ${project.status}`}>
                  {isBusy && <LoaderCircle size={12} className="spin" />}
                  {statusLabels[project.status]}
                </span>
                {isBusy ? (
                  <button
                    className="button secondary compact"
                    disabled={pending}
                    onClick={() => action("cancel")}
                  >
                    <Square size={13} /> Cancel
                  </button>
                ) : (
                  draft && (
                    <button
                      className="button primary compact"
                      disabled={
                        pending ||
                        (!dirty &&
                          project.rendered_revision === project.revision &&
                          project.status === "completed")
                      }
                      onClick={() => action("render")}
                    >
                      {pending ? (
                        <LoaderCircle size={15} className="spin" />
                      ) : (
                        <Play size={15} />
                      )}
                      {project.status === "completed" &&
                      !dirty &&
                      project.rendered_revision === project.revision
                        ? "Rendered"
                        : "Render video"}
                    </button>
                  )
                )}
              </div>
            </div>
            {isBusy && (
              <div className="job-progress" aria-live="polite">
                <div>
                  <LoaderCircle size={17} className="spin" />
                  <span>{project.detail}</span>
                  <strong>{project.progress}%</strong>
                </div>
                <progress
                  aria-label="Lesson generation progress"
                  max={100}
                  value={project.progress}
                />
                <small>
                  You can leave this page. Your lesson keeps working in the
                  background.
                </small>
              </div>
            )}
            {project.status === "failed" && (
              <div className="failure-panel" role="alert">
                <div>
                  <strong>This lesson needs another look.</strong>
                  <p>{project.error}</p>
                </div>
                <button
                  className="button secondary compact"
                  disabled={pending}
                  onClick={() => action("retry")}
                >
                  <RotateCcw size={15} /> Retry
                </button>
              </div>
            )}
            {project.status === "cancelled" && (
              <div className="failure-panel">
                <span>Job cancelled. Your saved work is here.</span>
                <button
                  className="button secondary compact"
                  disabled={pending}
                  onClick={() => action("retry")}
                >
                  <RotateCcw size={15} /> Resume
                </button>
              </div>
            )}
            <div className="lesson-grid">
              <section className="preview-column">
                <div className="section-label">
                  <span>
                    <Film size={14} />{" "}
                    {project.has_video ? "YOUR ANIMATION" : "THE VISUAL STORY"}
                  </span>
                  <span>16:9</span>
                </div>
                <div className="video-frame">
                  {project.has_video ? (
                    <video
                      key={`${project.id}-${project.rendered_revision}`}
                      controls
                      playsInline
                      preload="metadata"
                      src={`/api/projects/${project.id}/assets/video`}
                    >
                      <track
                        kind="captions"
                        label="English"
                        srcLang="en"
                        src={`/api/projects/${project.id}/assets/captions`}
                      />
                    </video>
                  ) : currentScene ? (
                    <SceneSketch scene={currentScene} number={sceneIndex + 1} />
                  ) : (
                    <div className="render-placeholder">
                      <Sparkles size={28} />
                      <h3>Planning your visual story.</h3>
                      <p>Your lesson’s scenes will appear here.</p>
                    </div>
                  )}
                </div>
                <div className="preview-meta">
                  <span>
                    {project.has_video ? (
                      <>
                        <Check size={14} /> {project.duration?.toFixed(0)} sec ·
                        Narrated MP4
                      </>
                    ) : (
                      <>
                        <Layers3 size={14} /> Storyboard sketch · Animation
                        appears after rendering
                      </>
                    )}
                  </span>
                  {project.has_video && (
                    <a
                      className="button secondary compact"
                      href={`/api/projects/${project.id}/assets/video?download=true`}
                    >
                      <Download size={14} /> Download MP4
                    </a>
                  )}
                </div>
                {project.has_video &&
                  (dirty || project.rendered_revision !== project.revision) && (
                    <p className="previous-export">
                      This preview shows the previous export. Render your
                      changes to update it.
                    </p>
                  )}
                {draft && (
                  <>
                    <div className="storyboard-heading">
                      <span>
                        <Layers3 size={15} /> STORYBOARD{" "}
                        <b>{draft.scenes.length} SCENES</b>
                      </span>
                      <span>Approx. {Math.round(wordCount / 2.5)} sec</span>
                    </div>
                    <div className="scene-list">
                      {draft.scenes.map((scene, index) => (
                        <button
                          key={index}
                          className={`scene-item ${sceneIndex === index ? "active" : ""}`}
                          onClick={() => setSceneIndex(index)}
                        >
                          <span className="scene-number">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <span>
                            <strong>{scene.title}</strong>
                            <small>{labels[scene.kind]}</small>
                          </span>
                          <ChevronRight size={15} />
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </section>
              <aside className="scene-editor">
                <div className="editor-heading">
                  <span>SCENE {String(sceneIndex + 1).padStart(2, "0")}</span>
                  <div>
                    <button
                      className="icon-button"
                      aria-label="Move scene earlier"
                      disabled={isBusy || sceneIndex === 0 || !draft}
                      onClick={() => moveScene(-1)}
                    >
                      <ArrowUp size={15} />
                    </button>
                    <button
                      className="icon-button"
                      aria-label="Move scene later"
                      disabled={
                        isBusy ||
                        !draft ||
                        sceneIndex >= draft.scenes.length - 1
                      }
                      onClick={() => moveScene(1)}
                    >
                      <ArrowDown size={15} />
                    </button>
                  </div>
                </div>
                {currentScene ? (
                  <>
                    <div className="editor-tabs">
                      <button
                        className={editorTab === "narration" ? "active" : ""}
                        onClick={() => setEditorTab("narration")}
                      >
                        <Volume2 size={14} /> Narration
                      </button>
                      <button
                        className={editorTab === "visuals" ? "active" : ""}
                        onClick={() => setEditorTab("visuals")}
                      >
                        <Layers3 size={14} /> Visuals
                      </button>
                    </div>
                    <fieldset disabled={isBusy || pending}>
                      {editorTab === "narration" ? (
                        <>
                          <label>
                            Scene title
                            <input
                              value={currentScene.title}
                              maxLength={60}
                              onChange={(event) =>
                                editScene({ title: event.target.value })
                              }
                            />
                          </label>
                          <label>
                            Voiceover script
                            <textarea
                              className="narration-editor"
                              value={currentScene.narration}
                              maxLength={650}
                              onChange={(event) =>
                                editScene({ narration: event.target.value })
                              }
                            />
                          </label>
                          <div className="editor-helper">
                            <Volume2 size={14} />
                            <span>
                              A natural English voice reads these words. Keep
                              each scene focused on one idea.
                            </span>
                          </div>
                          <div className="word-count">
                            {wordCount} / 190 words across the lesson
                          </div>
                        </>
                      ) : (
                        <>
                          <label>
                            Scene format
                            <select
                              value={currentScene.kind}
                              onChange={(event) =>
                                editScene({
                                  kind: event.target.value as SceneSpec["kind"],
                                })
                              }
                            >
                              {Object.entries(labels).map(([kind, name]) => (
                                <option key={kind} value={kind}>
                                  {name}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label>
                            On-screen labels
                            <textarea
                              rows={5}
                              value={currentScene.labels.join("\n")}
                              onChange={(event) =>
                                editScene({
                                  labels: event.target.value.split("\n"),
                                })
                              }
                            />
                          </label>
                          <p className="editor-caption">
                            One short label per line. Comparisons need exactly
                            two.
                          </p>
                          <label>
                            Equation or key statement
                            <input
                              value={currentScene.equation}
                              maxLength={90}
                              onChange={(event) =>
                                editScene({ equation: event.target.value })
                              }
                            />
                          </label>
                          {currentScene.kind === "graph" && (
                            <>
                              <label>
                                Function in x
                                <input
                                  value={currentScene.expression}
                                  onChange={(event) =>
                                    editScene({
                                      expression: event.target.value,
                                    })
                                  }
                                  maxLength={100}
                                  placeholder="x**2"
                                />
                              </label>
                              <div className="input-pair">
                                <label>
                                  Minimum x
                                  <input
                                    type="number"
                                    min={-10}
                                    max={9}
                                    value={currentScene.x_min}
                                    onChange={(event) =>
                                      editScene({
                                        x_min: Number(event.target.value),
                                      })
                                    }
                                  />
                                </label>
                                <label>
                                  Maximum x
                                  <input
                                    type="number"
                                    min={-9}
                                    max={10}
                                    value={currentScene.x_max}
                                    onChange={(event) =>
                                      editScene({
                                        x_max: Number(event.target.value),
                                      })
                                    }
                                  />
                                </label>
                              </div>
                            </>
                          )}
                          {currentScene.kind === "number_line" && (
                            <>
                              <label>
                                Array values
                                <input
                                  key={`${project.id}-${sceneIndex}-${currentScene.values.join(",")}`}
                                  defaultValue={currentScene.values.join(", ")}
                                  placeholder="2, 4, 6, 8, 10, 12, 14"
                                  onBlur={(event) => {
                                    const pieces = event.target.value
                                      .split(",")
                                      .map((value) => value.trim());
                                    const values = pieces.map(Number);
                                    if (
                                      pieces.some((value) => !value) ||
                                      values.length > 8 ||
                                      values.some(
                                        (value) =>
                                          !Number.isFinite(value) ||
                                          Math.abs(value) > 10000,
                                      )
                                    ) {
                                      setError(
                                        "Enter 1–8 comma-separated numbers between -10000 and 10000.",
                                      );
                                      event.target.value =
                                        currentScene.values.join(", ");
                                      return;
                                    }
                                    if (
                                      JSON.stringify(values) !==
                                      JSON.stringify(currentScene.values)
                                    )
                                      editScene({
                                        values,
                                        highlight_index:
                                          currentScene.highlight_index <
                                          values.length
                                            ? currentScene.highlight_index
                                            : -1,
                                      });
                                  }}
                                />
                              </label>
                              <label>
                                Highlighted element
                                <select
                                  value={currentScene.highlight_index}
                                  onChange={(event) =>
                                    editScene({
                                      highlight_index: Number(
                                        event.target.value,
                                      ),
                                    })
                                  }
                                >
                                  <option value={-1}>No highlight</option>
                                  {currentScene.values.map((value, index) => (
                                    <option key={index} value={index}>
                                      Index {index}: {value}
                                    </option>
                                  ))}
                                </select>
                              </label>
                            </>
                          )}
                        </>
                      )}
                    </fieldset>
                    <div className="save-area">
                      <span>
                        {dirty ? (
                          <>
                            <span className="unsaved-dot" /> Unsaved changes
                          </>
                        ) : (
                          <>
                            <Check size={13} /> Storyboard saved
                          </>
                        )}
                      </span>
                      <button
                        className="button secondary compact"
                        disabled={!dirty || isBusy || pending}
                        onClick={() => action("save")}
                      >
                        <Save size={14} /> Save
                      </button>
                    </div>
                  </>
                ) : (
                  <div className="editor-empty">
                    <Sparkles size={22} />
                    <h3>The story is taking shape.</h3>
                    <p>
                      Your scenes and narration will appear here when the
                      storyboard is ready.
                    </p>
                  </div>
                )}
              </aside>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
