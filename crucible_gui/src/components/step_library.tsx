import { useContext, useMemo, useState } from "react";
import { SchemaContext } from "@/context/api_context";
import type { StepConfig } from "@/types/workflows";
import type { StepSchema } from "@/types/step_schema";
import { getInitialParameters } from "./step_editor/model";

import { Box, ScrollArea, Stack, Text, TextInput, Tooltip, UnstyledButton } from "@mantine/core";
import { IconFlame, IconSearch } from "@tabler/icons-react";

type StepLibraryProps = {
    onSelect?: (step: StepConfig) => void;
};

export function StepLibrary({ onSelect }: StepLibraryProps) {
    const schema = useContext(SchemaContext)
    const [search, setSearch] = useState("");

    function exportStep(stepSchema: StepSchema): StepConfig {
        return {
            step_id: crypto.randomUUID(),
            key: stepSchema.key,
            description: stepSchema.default_description,
            name: stepSchema.default_name,
            parameters: getInitialParameters(stepSchema),
        };
    }

    const visibleSteps = useMemo(() => {
        const query = search.trim().toLowerCase();

        return schema
            .filter((step: StepSchema) => !step.key.startsWith("__"))
            .filter(
                (step) =>
                    query.length === 0 ||
                    step.default_name.toLowerCase().includes(query) ||
                    step.key.toLowerCase().includes(query),
            );
    }, [schema, search]);

    return (
        <Box
            className="fire-panel"
            p="sm"
            style={{ width: 240, flex: "0 0 240px", display: "flex", flexDirection: "column", height: "100%" }}
        >
            <Text
                size="xs"
                fw={700}
                tt="uppercase"
                c="ember.4"
                mb={8}
                style={{ letterSpacing: "0.06em" }}
            >
                Step library
            </Text>

            <TextInput
                placeholder="Search steps…"
                size="xs"
                mb={8}
                leftSection={<IconSearch size={13} />}
                value={search}
                onChange={(event) => setSearch(event.currentTarget.value)}
            />

            <ScrollArea style={{ flex: 1 }} offsetScrollbars type="auto">
                <Stack gap={2} pr={4}>
                    {visibleSteps.map((step) => (
                        <Tooltip
                            key={step.key}
                            label={step.default_description}
                            position="right"
                            withArrow
                            multiline
                            w={220}
                            openDelay={250}
                        >
                            <UnstyledButton
                                onClick={() => onSelect?.(exportStep(step))}
                                px={8}
                                py={7}
                                style={{
                                    borderRadius: "var(--mantine-radius-sm)",
                                    display: "flex",
                                    alignItems: "center",
                                    gap: 8,
                                    color: "#d5d2cc",
                                }}
                                className="workflow-row"
                            >
                                <IconFlame size={13} color="#f2600a" style={{ flex: "none" }} />
                                <Text size="xs" fw={500} truncate>
                                    {step.default_name}
                                </Text>
                            </UnstyledButton>
                        </Tooltip>
                    ))}

                    {visibleSteps.length === 0 && (
                        <Text size="xs" c="dimmed" ta="center" py="md">
                            No steps match “{search}”.
                        </Text>
                    )}
                </Stack>
            </ScrollArea>
        </Box>
    )
}
