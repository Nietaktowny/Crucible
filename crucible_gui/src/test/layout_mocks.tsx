import { createContext, useContext, useState, type ReactNode } from "react";
import type { ComboboxStore } from "@mantine/core";

// Keep business-interaction tests independent of jsdom's missing layout and
// Floating UI's positioning/focus observers. Production uses Mantine unchanged.
const MenuContext = createContext({
  opened: false,
  toggle: () => {},
  close: () => {},
});

function MenuRoot({
  children,
  opened: controlled,
  onChange,
}: {
  children: ReactNode;
  opened?: boolean;
  onChange?: (opened: boolean) => void;
}) {
  const [localOpened, setOpened] = useState(false);
  const opened = controlled ?? localOpened;
  const change = (value: boolean) => {
    setOpened(value);
    onChange?.(value);
  };
  return (
    <MenuContext.Provider
      value={{
        opened,
        toggle: () => change(!opened),
        close: () => change(false),
      }}
    >
      {children}
    </MenuContext.Provider>
  );
}

function MenuTarget({ children }: { children: ReactNode }) {
  const menu = useContext(MenuContext);
  return <span onClick={menu.toggle}>{children}</span>;
}

function MenuDropdown({ children }: { children: ReactNode }) {
  const menu = useContext(MenuContext);
  return menu.opened ? <div role="menu">{children}</div> : null;
}

function MenuItem({
  children,
  onClick,
}: {
  children: ReactNode;
  onClick?: () => void;
}) {
  const menu = useContext(MenuContext);
  return (
    <button
      type="button"
      role="menuitem"
      onClick={() => {
        onClick?.();
        menu.close();
      }}
    >
      {children}
    </button>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- compound test component
export const TestMenu = Object.assign(MenuRoot, {
  Target: MenuTarget,
  Dropdown: MenuDropdown,
  Item: MenuItem,
  Divider: () => <hr />,
});

export function TestOverlay({
  opened,
  title,
  children,
}: {
  opened: boolean;
  title: string;
  children: ReactNode;
}) {
  return opened ? (
    <section role="dialog" aria-label={title}>
      <h2>{title}</h2>
      {children}
    </section>
  ) : null;
}

type Choice = string | { value: string; label: string };
export function TestSelect({
  label,
  value,
  data = [],
  onChange,
}: {
  label?: string;
  value?: string | null;
  data?: Choice[];
  onChange?: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <select
        aria-label={label}
        value={value ?? ""}
        onChange={(event) => onChange?.(event.currentTarget.value)}
      >
        <option value="">Choose…</option>
        {data.map((choice) => {
          const option =
            typeof choice === "string"
              ? { value: choice, label: choice }
              : choice;
          return (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          );
        })}
      </select>
    </label>
  );
}

export function TestScrollArea({ children }: { children: ReactNode }) {
  return <div>{children}</div>;
}
// eslint-disable-next-line react-refresh/only-export-components -- compound test component
export const TestScroll = Object.assign(TestScrollArea, {
  Autosize: TestScrollArea,
});

const ComboboxContext = createContext<{
  store: ComboboxStore;
  onOptionSubmit: (value: string) => void;
} | null>(null);

function ComboboxRoot({
  children,
  store,
  onOptionSubmit,
}: {
  children: ReactNode;
  store: ComboboxStore;
  onOptionSubmit: (value: string) => void;
}) {
  return (
    <ComboboxContext.Provider value={{ store, onOptionSubmit }}>
      {children}
    </ComboboxContext.Provider>
  );
}

function ComboboxDropdown({ children }: { children: ReactNode }) {
  return useContext(ComboboxContext)?.store.dropdownOpened ? (
    <div>{children}</div>
  ) : null;
}

function ComboboxSearch({
  onChange,
  ...props
}: {
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  "aria-label": string;
}) {
  const context = useContext(ComboboxContext);
  return (
    <input
      aria-label={props["aria-label"]}
      value={props.value}
      onChange={onChange}
      onKeyDown={(event) => {
        if (event.key === "Escape") context?.store.closeDropdown();
      }}
    />
  );
}

function ComboboxOption({
  children,
  value,
  "aria-selected": selected,
}: {
  children: ReactNode;
  value: string;
  "aria-selected": boolean;
}) {
  const context = useContext(ComboboxContext);
  return (
    <div
      role="option"
      aria-selected={selected}
      onClick={() => context?.onOptionSubmit(value)}
    >
      {children}
    </div>
  );
}

// eslint-disable-next-line react-refresh/only-export-components -- compound test component
export const TestCombobox = Object.assign(ComboboxRoot, {
  Target: TestScrollArea,
  Dropdown: ComboboxDropdown,
  Search: ComboboxSearch,
  Options: ({ children }: { children: ReactNode }) => (
    <div role="listbox" aria-multiselectable="true">
      {children}
    </div>
  ),
  Option: ComboboxOption,
  Footer: TestScrollArea,
  Empty: TestScrollArea,
  Chevron: () => <span />,
});
