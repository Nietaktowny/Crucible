import { useMemo, useEffect } from "react";
import {
  ReactFlow,
  Controls,
  useReactFlow,
  MarkerType,
  type Edge,
  type NodeMouseHandler,
} from "@xyflow/react";

import "@xyflow/react/dist/style.css";

import type { StepConfig } from "@/types/workflows";
import { StepNode } from "@/components/step_graph_node";
import type { StepNodeType } from "@/components/step_graph_node";

type WorkflowEdge = Edge;

type WorkflowGraphProps = {
  steps: StepConfig[];
  selectedStepId?: string | null;
  onSelect: (step: StepConfig) => void;
};

const NODE_TYPES = { stepNode: StepNode };

const EDGE_DEFAULTS = {
  type: "smoothstep",
  animated: true,
  markerEnd: {
    type: MarkerType.ArrowClosed,
    color: "#ff9d3d",
    width: 16,
    height: 16,
  },
} as const;

export function WorkflowGraph({
  steps,
  selectedStepId,
  onSelect,
}: WorkflowGraphProps) {
  const nodes = useMemo<StepNodeType[]>(
    () =>
      steps.map((step, index) => ({
        id: step.step_id,
        type: "stepNode",
        position: { x: 0, y: index * 92 },
        selected: step.step_id === selectedStepId,
        data: { step, index: index + 1 },
      })),
    [steps, selectedStepId],
  );
  const edges = useMemo<WorkflowEdge[]>(
    () =>
      steps.slice(0, -1).map((step, index) => ({
        id: `${step.step_id}-${steps[index + 1].step_id}`,
        source: step.step_id,
        target: steps[index + 1].step_id,
        ...EDGE_DEFAULTS,
      })),
    [steps],
  );

  const onNodeClick: NodeMouseHandler<StepNodeType> = (_, node) => {
    onSelect(node.data.step);
  };

  return (
    <div className="workflow-graph-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        nodesDraggable={false}
        nodesConnectable={false}
        edgesReconnectable={false}
        deleteKeyCode={null}
        onNodeClick={onNodeClick}
        proOptions={{ hideAttribution: true }}
        fitView
        fitViewOptions={{ padding: 0.3 }}
      >
        <Controls showInteractive={false} />
        <RefitOnPanelToggle
          panelOpen={selectedStepId !== null && selectedStepId !== undefined}
          nodeCount={nodes.length}
        />
      </ReactFlow>
    </div>
  );
}

/**
 * The graph container's width changes when the step editor side panel opens
 * or closes; ReactFlow only auto-fits on mount, so re-fit explicitly on that
 * transition or newly added nodes end up clipped behind the old viewport.
 */
function RefitOnPanelToggle({
  panelOpen,
  nodeCount,
}: {
  panelOpen: boolean;
  nodeCount: number;
}) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void fitView({ padding: 0.3, duration: 250 });
    }, 50);

    return () => window.clearTimeout(timeoutId);
  }, [panelOpen, nodeCount, fitView]);

  return null;
}
