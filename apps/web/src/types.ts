export type SceneKind =
  "concept" | "steps" | "graph" | "comparison" | "number_line" | "geometry";

export interface SceneSpec {
  kind: SceneKind;
  title: string;
  narration: string;
  labels: string[];
  equation: string;
  expression: string;
  x_min: number;
  x_max: number;
  values: number[];
  highlight_index: number;
}

export interface Storyboard {
  title: string;
  objective: string;
  scenes: SceneSpec[];
}

export interface User {
  id: string;
  email: string;
}
export type ProjectStatus =
  | "queued"
  | "planning"
  | "draft"
  | "narrating"
  | "rendering"
  | "assembling"
  | "completed"
  | "failed"
  | "cancelled";
export interface Project {
  id: string;
  topic: string;
  audience: "beginner" | "intermediate";
  title: string;
  status: ProjectStatus;
  operation: "plan" | "render";
  revision: number;
  rendered_revision: number;
  progress: number;
  detail: string;
  error: string | null;
  duration: number | null;
  provider: string | null;
  created_at: number;
  updated_at: number;
  example: boolean;
  has_video: boolean;
  storyboard?: Storyboard | null;
}

export const busy = (project?: Project | null) =>
  !!project &&
  ["queued", "planning", "narrating", "rendering", "assembling"].includes(
    project.status,
  );
