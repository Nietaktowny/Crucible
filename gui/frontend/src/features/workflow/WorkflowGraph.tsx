import {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import type { Workflow } from "@/features/workflow/types";

type StepNodeData = {
  index: number;
  key: string;
  name: string;
  description: string;
};

function StepNode({ data, selected }: NodeProps<Node<StepNodeData>>) {
  return (
    <div
      className={[
        "w-56 rounded-xl border px-4 py-3 shadow-md",
        "bg-card text-card-foreground",
        selected ? "border-primary ring-2 ring-primary/40" : "border-border",
      ].join(" ")}
    >
      <Handle type="target" position={Position.Top} />

      <div className="text-xs text-muted-foreground">
        {String(data.index + 1).padStart(2, "0")} · {data.key}
      </div>

      <div className="mt-1 text-sm font-semibold">{data.name}</div>

      <div className="mt-2 line-clamp-2 text-xs text-muted-foreground">
        {data.description}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = {
  step: StepNode,
};

type WorkflowGraphProps = {
  workflow: Workflow;
  selectedStepId: string | null;
  onSelectStep: (stepId: string | null) => void;
};

export default function WorkflowGraph({
  workflow,
  selectedStepId,
  onSelectStep,
}: WorkflowGraphProps) {
  const nodes: Node<StepNodeData>[] = workflow.steps.map((step, index) => ({
    id: step.id,
    type: "step",
    position: {
      x: 120,
      y: index * 140,
    },
    selected: step.id === selectedStepId,
    data: {
      index,
      key: step.key,
      name: step.name,
      description: step.description,
    },
  }));

  const edges: Edge[] = workflow.steps.slice(1).map((step, index) => ({
    id: `${workflow.steps[index].id}-${step.id}`,
    source: workflow.steps[index].id,
    target: step.id,
    type: "smoothstep",
    animated: true,
    markerEnd: {
      type: MarkerType.ArrowClosed,
    },
  }));

  return (
    <div className="h-full w-full bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable
        onNodeClick={(_, node) => onSelectStep(node.id)}
        onPaneClick={() => onSelectStep(null)}
      >
        <Background />

        <MiniMap
          pannable
          zoomable
          className="!bg-background"
          maskColor="hsl(var(--background) / 0.65)"
          nodeColor="hsl(var(--muted))"
        />

        <Controls className="!bg-card !text-foreground" />
      </ReactFlow>
    </div>
  );
}