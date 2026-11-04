import type { ReactNode } from "react";

// The dark head of every inner sheet; it continues the site header
export function PageHead({ title, children, side }: { title: ReactNode; children?: ReactNode; side?: ReactNode }) {
  return (
    <div className="sheet-head">
      <div className={`frame ${side ? "sheet-head-split" : ""}`}>
        <div>
          <h1>{title}</h1>
          {children}
        </div>
        {side}
      </div>
    </div>
  );
}
