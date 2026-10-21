import { css } from "lit";
export const styles = css`
  :host {
    --bg: var(--primary-background-color, Canvas);
    --surface: var(--ha-card-background, var(--card-background-color, Canvas));
    --text: var(--primary-text-color, CanvasText);
    --secondary: var(--secondary-text-color, GrayText);
    --line: var(--divider-color, #dce0e5);
    --accent: var(--primary-color, #03a9f4);
    --selected: color-mix(in srgb, var(--accent) 10%, var(--surface));
    display: flex;
    flex-direction: column;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
    background: var(--bg);
    color: var(--text);
    font-family: var(--ha-font-family-body, Roboto, system-ui, sans-serif);
    font-size: var(--ha-font-size-m, 14px);
    line-height: 1.6;
    color-scheme: inherit;
  }
  * {
    box-sizing: border-box;
    scrollbar-width: thin;
  }
  :focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 3px;
  }
  [hidden] {
    display: none !important;
  }
  header {
    display: flex;
    align-items: center;
    gap: 24px;
    min-height: 60px;
    padding: 0 20px;
    background: var(--app-header-background-color, var(--surface));
    color: var(--app-header-text-color, var(--text));
    border-bottom: 1px solid var(--line);
    flex-shrink: 0;
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-shrink: 0;
  }
  .brand svg {
    width: 25px;
    height: 25px;
    fill: currentColor;
  }
  h1 {
    font-size: 20px;
    margin: 0;
    letter-spacing: -0.02em;
  }
  h2 {
    font-size: 22px;
    line-height: 1.3;
    margin: 0 0 12px;
  }
  h3 {
    font-size: 16px;
    margin: 0 0 12px;
  }
  h2,
  h3,
  strong {
    overflow-wrap: anywhere;
  }
  p {
    margin: 8px 0 16px;
  }
  .help,
  small {
    color: var(--secondary);
  }
  .help {
    max-width: 75ch;
  }
  small {
    font-size: 12px;
    overflow-wrap: anywhere;
  }
  code {
    font-size: 12px;
    overflow-wrap: anywhere;
  }
  .grow {
    flex: 1;
    min-width: 0;
  }
  nav {
    display: flex;
    align-self: stretch;
    gap: 8px;
    min-width: 0;
  }
  nav button {
    position: relative;
    background: transparent;
    color: inherit;
    border: 0;
    border-radius: 0;
    padding: 12px 16px;
  }
  nav button[aria-current="page"]:after {
    content: "";
    position: absolute;
    inset-inline: 16px;
    bottom: 0;
    height: 3px;
    background: currentColor;
  }
  .sidebar-toggle {
    width: 48px;
    min-width: 48px;
    height: 48px;
    border: 0;
    background: transparent;
    color: inherit;
    padding: 12px;
  }
  .sidebar-toggle svg {
    width: 24px;
    fill: currentColor;
  }
  main {
    display: flex;
    flex: 1;
    min-height: 0;
    min-width: 0;
    overflow: hidden;
  }
  .workspace {
    display: grid;
    grid-template-columns: 280px minmax(0, 1fr);
    flex: 1;
    min-height: 0;
  }
  .rail {
    background: var(--surface);
    border-inline-end: 1px solid var(--line);
    padding: 16px 12px;
    overflow: auto;
    min-width: 0;
  }
  .detail {
    overflow: auto;
    min-width: 0;
    padding: 24px;
    scroll-padding: 16px;
  }
  .page {
    overflow: auto;
    flex: 1;
    min-width: 0;
    padding: 24px;
  }
  .page > section,
  .page > h2,
  .page > .help {
    max-width: 980px;
    margin-inline: auto;
  }
  .page > section {
    margin-bottom: 28px;
  }
  .row,
  .actions {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
  .section-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }
  .section-heading h2,
  .section-heading h3 {
    margin: 0;
  }
  .section {
    padding: 20px 0;
    border-bottom: 1px solid var(--line);
  }
  .section:first-child {
    padding-top: 0;
  }
  .section:last-child {
    border-bottom: 0;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 230px), 1fr));
    gap: 4px 20px;
  }
  .device {
    margin: 12px 0;
    padding: 12px 0 12px 16px;
    border-inline-start: 2px solid var(--line);
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin: 8px 0;
    min-width: 0;
  }
  .check {
    flex-direction: row;
    align-items: center;
    gap: 10px;
    min-height: 30px;
    cursor: pointer;
  }
  .check input {
    width: 18px;
    height: 18px;
    min-height: 18px;
    flex-shrink: 0;
    accent-color: var(--accent);
  }
  input,
  textarea,
  select,
  button {
    font: inherit;
    color: inherit;
  }
  input,
  textarea,
  select {
    width: 100%;
    min-width: 0;
    min-height: 40px;
    padding: 8px 10px;
    background: var(--input-fill-color, var(--surface));
    border: 1px solid var(--input-outlined-idle-border-color, var(--line));
    border-radius: 8px;
    color: var(--input-ink-color, var(--text));
  }
  textarea {
    resize: vertical;
    min-height: 90px;
  }
  input:invalid {
    border-color: var(--error-color, #db4437);
  }
  button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 38px;
    padding: 7px 12px;
    max-width: 100%;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    cursor: pointer;
    line-height: 1.4;
  }
  button:hover:not(:disabled) {
    background: var(--selected);
  }
  button:disabled {
    opacity: 0.55;
    cursor: default;
  }
  button.primary {
    background: var(--accent);
    color: var(--text-primary-color, #fff);
    border-color: transparent;
  }
  button.danger {
    color: var(--error-color, #db4437);
  }
  .link {
    border: 0;
    background: transparent;
  }
  .field {
    min-width: 0;
    margin: 8px 0;
  }
  .field > span {
    display: block;
    margin-bottom: 6px;
  }
  ha-entity-picker,
  ha-selector {
    display: block;
    min-width: 0;
  }
  .choices {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 210px), 1fr));
    gap: 0 12px;
  }
  .choices .check {
    margin: 4px 0;
    overflow-wrap: anywhere;
  }
  fieldset {
    border: 0;
    padding: 0;
    margin: 8px 0;
    min-width: 0;
  }
  legend {
    padding: 0;
    margin-bottom: 4px;
    font-weight: 500;
  }
  .filters {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
    margin: 12px 0;
  }
  .filters button {
    padding: 6px 9px;
    border: 0;
    background: transparent;
    font-size: 12px;
  }
  .filters button[aria-pressed="true"] {
    background: var(--selected);
    color: var(--accent);
  }
  .notification-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .notification-list button {
    width: 100%;
    text-align: start;
    align-items: start;
    justify-content: start;
    flex-direction: column;
    border: 0;
    padding: 12px 10px;
    margin: 3px 0;
    background: transparent;
  }
  .notification-list button[aria-pressed="true"] {
    background: var(--selected);
  }
  .notification-list strong {
    font-weight: 500;
  }
  .badge {
    display: inline-block;
    font-size: 12px;
    color: var(--secondary);
  }
  .pending {
    color: var(--warning-color, #b87500);
  }
  .accepted,
  .resolved {
    color: var(--success-color, #2e7d32);
  }
  .failed {
    color: var(--error-color, #db4437);
  }
  .empty {
    max-width: 520px;
    margin: 8vh auto;
    padding: 24px;
  }
  .empty p {
    color: var(--secondary);
  }
  .back {
    display: none;
    margin-bottom: 16px;
  }
  .metadata {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
    gap: 16px;
    margin: 20px 0;
  }
  .metadata dt {
    font-size: 12px;
    color: var(--secondary);
  }
  .metadata dd {
    margin: 2px 0;
    overflow-wrap: anywhere;
  }
  .delivery {
    padding: 12px 0;
    border-bottom: 1px solid var(--line);
  }
  .delivery .row {
    justify-content: space-between;
  }
  .timeline {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .timeline li {
    border-inline-start: 2px solid var(--line);
    margin: 0 0 8px;
    padding: 6px 14px;
  }
  .body {
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }
  .notice {
    padding: 12px 16px;
    margin: 10px 20px;
    background: var(--selected);
    border: 1px solid var(--line);
    border-radius: 8px;
    flex-shrink: 0;
    overflow-wrap: anywhere;
  }
  .notice.error {
    color: var(--error-color, #db4437);
  }
  .savebar {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 20px calc(12px + env(safe-area-inset-bottom, 0px));
    border-top: 1px solid var(--line);
    background: var(--surface);
  }
  .savebar .grow {
    line-height: 1.4;
  }
  details {
    margin: 12px 0;
  }
  summary {
    cursor: pointer;
    min-height: 40px;
    padding: 8px 0;
    font-weight: 500;
  }
  details[open] > summary {
    margin-bottom: 8px;
  }
  .result {
    margin-top: 20px;
    border-top: 1px solid var(--line);
    padding-top: 16px;
  }
  .result ul {
    padding-inline-start: 20px;
  }
  .result li {
    overflow-wrap: anywhere;
  }
  .result dl {
    margin: 4px 0 8px 12px;
  }
  .result dt {
    font-size: 12px;
    color: var(--secondary);
  }
  .result dd {
    margin: 0 0 6px;
    overflow-wrap: anywhere;
  }
  .confirm {
    padding: 12px;
    border: 1px solid var(--line);
    border-radius: 8px;
  }
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
  }
  @media (max-width: 1100px) {
    .workspace {
      grid-template-columns: 240px minmax(0, 1fr);
    }
    .detail {
      padding: 20px;
    }
  }
  @media (max-width: 760px) {
    header {
      gap: 8px;
      padding: 4px 12px 0;
      flex-wrap: wrap;
      min-height: 60px;
    }
    .brand {
      gap: 8px;
    }
    h1 {
      font-size: 18px;
    }
    nav {
      width: 100%;
      gap: 2px;
      overflow: auto;
    }
    nav button {
      padding: 10px 8px;
      font-size: 12px;
      flex: 1;
      white-space: nowrap;
    }
    nav button[aria-current="page"]:after {
      inset-inline: 8px;
    }
    .workspace {
      display: block;
      overflow: hidden;
    }
    .rail {
      height: 100%;
      border: 0;
    }
    .workspace:not(.has-detail) .detail {
      display: none;
    }
    .workspace.has-detail .rail {
      display: none;
    }
    .workspace.has-detail .detail {
      height: 100%;
    }
    .detail,
    .page {
      padding: 18px 14px;
    }
    .back {
      display: inline-flex;
    }
    h2 {
      font-size: 20px;
    }
    .savebar {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      padding: 10px 14px calc(10px + env(safe-area-inset-bottom, 0px));
    }
    .savebar .grow {
      grid-column: 1/-1;
      font-size: 12px;
    }
    .notice {
      margin: 8px 12px;
    }
    .empty {
      margin: 24px auto;
      padding: 14px;
    }
    .section-heading {
      flex-wrap: wrap;
    }
    .choices {
      grid-template-columns: 1fr;
    }
  }
  @media (pointer: coarse) {
    button,
    input,
    select,
    summary {
      min-height: 44px;
    }
    .check input {
      min-height: 20px;
      width: 20px;
      height: 20px;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    * {
      scroll-behavior: auto !important;
      transition: none !important;
    }
  }
`;
