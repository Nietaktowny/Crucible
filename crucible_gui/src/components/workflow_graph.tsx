import { useState, useCallback, useEffect } from "react";
import {
  ReactFlow,
  Controls,
  useReactFlow,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  MarkerType,
  type Edge,
  type NodeChange,
  type EdgeChange,
  type Connection,
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
}

const EDGE_DEFAULTS = {
  type: "smoothstep",
  animated: true,
  markerEnd: { type: MarkerType.ArrowClosed, color: "#ff9d3d", width: 16, height: 16 },
} as const;

export function WorkflowGraph({ steps, selectedStepId, onSelect }: WorkflowGraphProps) {
  const [nodes, setNodes] = useState<StepNodeType[]>(getNodes(steps));
  const [edges, setEdges] = useState<WorkflowEdge[]>(getEdges(steps));
  const nodeTypes = {
    stepNode: StepNode,
  };

  function getNodes(steps: StepConfig[]): StepNodeType[] {
    return steps.map((step, index) => ({
      id: step.step_id,
      type: 'stepNode',
      position: {
        x: 0,
        y: index * 92,
      },
      selected: step.step_id === selectedStepId,
      data: {
        step: step,
        index: index + 1,
      },
    }));
  }

  function getEdges(steps: StepConfig[]): WorkflowEdge[] {
    return steps.slice(0, -1).map((step, index) => {
      const nextStep = steps[index + 1];

      return {
        id: `${step.step_id}-${nextStep.step_id}`,
        source: step.step_id,
        target: nextStep.step_id,
        ...EDGE_DEFAULTS,
      };
    });
  }

  const onNodesChange = useCallback(
    (changes: NodeChange<StepNodeType>[]) =>
      setNodes((nodesSnapshot) =>
        applyNodeChanges(changes, nodesSnapshot)
      ),
    [],
  );

  const onEdgesChange = useCallback(
    (changes: EdgeChange<WorkflowEdge>[]) =>
      setEdges((edgesSnapshot) =>
        applyEdgeChanges(changes, edgesSnapshot)
      ),
    [],
  );

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((edgesSnapshot) =>
        addEdge({ ...params, ...EDGE_DEFAULTS }, edgesSnapshot)
      ),
    [],
  );

  const onNodeClick: NodeMouseHandler<StepNodeType> = (_, node) => {
    onSelect(node.data.step)
  };

  useEffect(() => {
    setNodes(getNodes(steps))
    setEdges(getEdges(steps))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [steps, selectedStepId])

  return (
    <div className="workflow-graph-container">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
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
function RefitOnPanelToggle({ panelOpen, nodeCount }: { panelOpen: boolean; nodeCount: number }) {
  const { fitView } = useReactFlow();

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void fitView({ padding: 0.3, duration: 250 });
    }, 50);

    return () => window.clearTimeout(timeoutId);
  }, [panelOpen, nodeCount, fitView]);

  return null;
}
