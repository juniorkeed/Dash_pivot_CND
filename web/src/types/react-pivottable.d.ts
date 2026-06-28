declare module "react-pivottable/PivotTable" {
  import type { ComponentType } from "react";
  const PivotTable: ComponentType<any>;
  export default PivotTable;
}

declare module "react-pivottable/PivotTableUI" {
  import type { ComponentType } from "react";
  const PivotTableUI: ComponentType<any>;
  export default PivotTableUI;
}

declare module "react-pivottable/TableRenderers" {
  const TableRenderers: Record<string, unknown>;
  export default TableRenderers;
}

declare module "react-pivottable/Utilities" {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export const aggregatorTemplates: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  export const aggregators: any;
  export function numberFormat(opts?: Record<string, unknown>): (x: number) => string;
}

declare module "react-pivottable";
