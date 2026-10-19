/** Maps each catalog entry to the component that draws it. A new component is added here and in schemas.ts. */
import type { ReactElement } from "react";
import { CodeHighlight } from "../components/CodeHighlight";
import { EndCard } from "../components/EndCard";
import { Illustration } from "../components/Illustration";
import { MetricCards } from "../components/MetricCards";
import { ScreenRecording } from "../components/ScreenRecording";
import { Statement } from "../components/Statement";
import { Terminal } from "../components/Terminal";
import { TitleCard } from "../components/TitleCard";
import type { TimedScene } from "./schemas";

/** Draw one scene. The switch is exhaustive: a component missing here does not compile. */
export const renderScene = (timedScene: TimedScene): ReactElement => {
  const { scene } = timedScene;
  switch (scene.component) {
    case "TitleCard":
      return <TitleCard {...scene.props} />;
    case "EndCard":
      return <EndCard {...scene.props} />;
    case "ScreenRecording":
      return (
        <ScreenRecording
          sceneId={scene.id}
          footage={timedScene.footage}
          keyPhrases={scene.props.key_phrases}
        />
      );
    case "Statement":
      return <Statement {...scene.props} />;
    case "CodeHighlight":
      return (
        <CodeHighlight {...scene.props} sceneId={scene.id} codeLines={timedScene.code_lines} />
      );
    case "Terminal":
      return (
        <Terminal {...scene.props} sceneId={scene.id} terminalLines={timedScene.terminal_lines} />
      );
    case "MetricCards":
      return <MetricCards {...scene.props} />;
    case "Illustration":
      return <Illustration {...scene.props} />;
    default: {
      const unhandledScene: never = scene;
      throw new Error(`no component for scene ${JSON.stringify(unhandledScene)}`);
    }
  }
};
