import { useParams } from "react-router-dom";

import { WorkflowDetails } from "@/components/workflow_details";

export function WorkflowEditPage() {
    const params = useParams();
    const workflowId = params.workflowId || null;

    return <WorkflowDetails selectedWorkflow={workflowId} />;
}
