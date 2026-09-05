import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import type { StepConfig } from "@/types/workflows";

export type StepNodeData = {
  step: StepConfig;
  index: number;
};

export type StepNodeType = Node<StepNodeData, "stepNode">;

export function StepNode({ data, selected }: NodeProps<StepNodeType>) {
  return (
    <div className={`step-node${selected ? " selected" : ""}`}>
      <Handle type="target" position={Position.Top} />

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span className="step-node-index">{data.index}</span>
        <div style={{ minWidth: 0 }}>
          <div className="step-node-title">{data.step.name || data.step.key}</div>
          {data.step.description && (
            <div className="step-node-desc">{data.step.description}</div>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
