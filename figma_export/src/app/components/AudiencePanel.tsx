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
  integrated: "bg-[#E6F5F6] text-[#0D7680] border-[#0D7680]/30",
  planned:    "bg-[#FEF0E6] text-[#C05A0B] border-[#C05A0B]/30",
  mock:       "bg-[#F2EDE8] text-[#66605A] border-[#D9D0C7]",
};

export function AudiencePanel({ audience }: AudiencePanelProps) {
  const [open, setOpen] = useState(false);
  const config = audienceConfig[audience];

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <div className="mt-3 border border-[#D9D0C7] bg-[#FFF9F5] overflow-hidden">
        <div className="px-3 py-2">
          <p className="text-sm text-[#1A1816]">
            <span className="font-medium capitalize">{audience} View:</span>{" "}
            {config.description}
          </p>
        </div>

        <CollapsibleTrigger className="w-full px-3 py-2 flex items-center gap-2 text-xs text-[#66605A] hover:bg-[#F2EDE8] transition-colors border-t border-[#D9D0C7]">
          <ChevronDown className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`} />
          <span>Use cases & data sources</span>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <div className="px-3 pb-3 pt-1 space-y-3 border-t border-[#D9D0C7]">
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <HelpCircle className="w-3.5 h-3.5 text-[#990F3D]" />
                <span className="text-xs font-semibold text-[#1A1816]">Use cases</span>
              </div>
              <ul className="space-y-1">
                {config.useCases.map((uc) => (
                  <li key={uc.id} className="text-xs text-[#66605A] flex items-start gap-2">
                    <span className="text-[#A89E94] mt-0.5">–</span>
                    <span>{uc.question}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Database className="w-3.5 h-3.5 text-[#990F3D]" />
                <span className="text-xs font-semibold text-[#1A1816]">Data sources</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {config.resources.map((r) => (
                  <span
                    key={r.id}
                    className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs border ${resourceStatusColors[r.status] || "bg-[#F2EDE8]"}`}
                    title={r.notes}
                  >
                    {r.name}
                    <span className="opacity-60">({r.status})</span>
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
