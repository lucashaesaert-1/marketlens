import { ChevronDown, HelpCircle, Database } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";
import { useState } from "react";
import { audienceConfig, type Audience } from "../data/audienceConfig";

interface AudiencePanelProps {
  audience: Audience;
}

const resourceStatusColors: Record<string, string> = {
  integrated: "bg-emerald-100 text-emerald-700 border-emerald-200",
  planned: "bg-amber-100 text-amber-700 border-amber-200",
  mock: "bg-slate-100 text-slate-600 border-slate-200",
};

export function AudiencePanel({ audience }: AudiencePanelProps) {
  const [open, setOpen] = useState(false);
  const config = audienceConfig[audience];

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="mt-3 rounded-lg border border-indigo-100 bg-indigo-50/50 overflow-hidden">
        <div className="px-3 py-2">
          <p className="text-sm text-indigo-900">
            <span className="font-medium capitalize">{audience} View:</span>{" "}
            {config.description}
          </p>
        </div>

        <CollapsibleTrigger className="w-full px-3 py-2 flex items-center gap-2 text-xs text-indigo-600 hover:bg-indigo-100/50 transition-colors">
          <ChevronDown
            className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
          />
          <span>Use cases & data sources</span>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-3 pb-3 pt-1 space-y-3 border-t border-indigo-100">
            {/* Use Cases */}
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
                <span className="text-xs font-semibold text-indigo-900">
                  Use cases
                </span>
              </div>
              <ul className="space-y-1">
                {config.useCases.map((uc) => (
                  <li
                    key={uc.id}
                    className="text-xs text-indigo-800 flex items-start gap-2"
                  >
                    <span className="text-indigo-400 mt-0.5">•</span>
                    <span>{uc.question}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Resources */}
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Database className="w-3.5 h-3.5 text-indigo-600" />
                <span className="text-xs font-semibold text-indigo-900">
                  Data sources
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {config.resources.map((r) => (
                  <span
                    key={r.id}
                    className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs border ${resourceStatusColors[r.status] || "bg-slate-100"}`}
                    title={r.notes}
                  >
                    {r.name}
                    <span className="opacity-75">({r.status})</span>
                  </span>
                ))}
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
