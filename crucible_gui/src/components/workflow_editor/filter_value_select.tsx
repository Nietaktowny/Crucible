import {
  Alert,
  Button,
  Checkbox,
  Combobox,
  Group,
  Input,
  InputBase,
  Loader,
  Text,
  useCombobox,
} from "@mantine/core";

import { displayValue } from "./model";

type Props = {
  values: unknown[];
  chosen: unknown[];
  search: string;
  loading: boolean;
  error: string | null;
  truncated: boolean;
  onSearch: (search: string) => void;
  onChange: (values: unknown[]) => void;
};

export function FilterValueSelect({
  values,
  chosen,
  search,
  loading,
  error,
  truncated,
  onSearch,
  onChange,
}: Props) {
  const combobox = useCombobox({
    onDropdownOpen: () => combobox.focusSearchInput(),
    onDropdownClose: () => combobox.resetSelectedOption(),
  });
  const selected = new Set(chosen.map((value) => JSON.stringify(value)));

  function toggle(token: string) {
    const index = values.findIndex((value) => JSON.stringify(value) === token);
    if (index < 0) return;
    onChange(
      selected.has(token)
        ? chosen.filter((value) => JSON.stringify(value) !== token)
        : [...chosen, values[index]],
    );
  }

  return (
    <Input.Wrapper label="Values to keep">
      <Combobox
        store={combobox}
        withinPortal={false}
        onOptionSubmit={(token) => toggle(String(token))}
      >
        <Combobox.Target>
          <InputBase
            component="button"
            type="button"
            pointer
            aria-label="Values to keep"
            rightSection={<Combobox.Chevron />}
            rightSectionPointerEvents="none"
            onClick={() => combobox.toggleDropdown()}
          >
            {chosen.length ? (
              `${chosen.length} ${chosen.length === 1 ? "value" : "values"} selected`
            ) : (
              <Input.Placeholder>Select values…</Input.Placeholder>
            )}
          </InputBase>
        </Combobox.Target>
        <Combobox.Dropdown>
          <Combobox.Search
            aria-label="Search all data values"
            placeholder="Search all data values"
            value={search}
            onChange={(event) => {
              onSearch(event.currentTarget.value);
              combobox.resetSelectedOption();
            }}
            rightSection={loading ? <Loader size="xs" /> : undefined}
          />
          {error && (
            <Alert color="red" p="xs">
              {error}
            </Alert>
          )}
          <Combobox.Options
            aria-label="Values to keep"
            aria-multiselectable="true"
            style={{ maxHeight: 220, overflowY: "auto" }}
          >
            {values.map((value) => {
              const token = JSON.stringify(value);
              const checked = selected.has(token);
              return (
                <Combobox.Option
                  key={token}
                  value={token}
                  active={checked}
                  aria-selected={checked}
                >
                  <Group gap="sm" wrap="nowrap">
                    <Checkbox.Indicator checked={checked} aria-hidden />
                    <Text size="sm" style={{ overflowWrap: "anywhere" }}>
                      {displayValue(value)}
                    </Text>
                  </Group>
                </Combobox.Option>
              );
            })}
            {!values.length && !loading && !error && (
              <Combobox.Empty>No matching values</Combobox.Empty>
            )}
          </Combobox.Options>
          <Combobox.Footer>
            <Group gap="xs" justify="space-between">
              <Button
                size="xs"
                variant="default"
                disabled={!values.length || loading}
                onClick={() =>
                  onChange([
                    ...chosen,
                    ...values.filter(
                      (value) => !selected.has(JSON.stringify(value)),
                    ),
                  ])
                }
              >
                Select listed values
              </Button>
              <Button
                size="xs"
                variant="subtle"
                disabled={!chosen.length}
                onClick={() => onChange([])}
              >
                Clear selection
              </Button>
            </Group>
            {truncated && (
              <Text size="xs" c="dimmed" mt="xs">
                First 100 matching values. Search to find more.
              </Text>
            )}
            <Text size="xs" c="dimmed" mt="xs">
              Null and empty text are separate values. Selections stay selected
              when searching.
            </Text>
          </Combobox.Footer>
        </Combobox.Dropdown>
      </Combobox>
    </Input.Wrapper>
  );
}
