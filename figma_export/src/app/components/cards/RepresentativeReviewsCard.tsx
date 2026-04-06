import { ThumbsUp, ThumbsDown } from "lucide-react";

interface Review {
  company: string;
  rating: number;
  sentiment: "positive" | "negative";
  text: string;
  date: string | null;
}

interface Props {
  reviews: Review[];
  colorMap?: Record<string, string>;
}

function StarRating({ rating }: { rating: number }) {
  const full = Math.round(rating);
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <span key={i} className={`text-[11px] ${i <= full ? "text-[#F2720C]" : "text-[#D9D0C7]"}`}>
          ★
        </span>
      ))}
      <span className="ml-1 text-[11px] text-[#66605A]">{rating.toFixed(1)}</span>
    </span>
  );
}

export function RepresentativeReviewsCard({ reviews, colorMap = {} }: Props) {
  if (!reviews || reviews.length === 0) return null;

  // Group by company
  const byCompany: Record<string, Review[]> = {};
  for (const r of reviews) {
    if (!byCompany[r.company]) byCompany[r.company] = [];
    byCompany[r.company].push(r);
  }

  const companies = Object.keys(byCompany);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {companies.map((company) => {
        const color = colorMap[company] ?? "#64748b";
        const companyReviews = byCompany[company];
        return (
          <div
            key={company}
            className="border border-[#D9D0C7] rounded-sm overflow-hidden"
          >
            {/* Company header */}
            <div
              className="px-4 py-2.5 flex items-center gap-2"
              style={{ borderLeft: `3px solid ${color}`, background: "#FAFAF9" }}
            >
              <span className="text-xs font-semibold text-[#1A1816]">{company}</span>
            </div>

            {/* Reviews */}
            <div className="divide-y divide-[#F0EBE6]">
              {companyReviews.map((review, i) => (
                <div key={i} className="px-4 py-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <StarRating rating={review.rating} />
                    <div className="flex items-center gap-1.5">
                      {review.sentiment === "positive" ? (
                        <ThumbsUp className="w-3 h-3 text-[#00994D]" />
                      ) : (
                        <ThumbsDown className="w-3 h-3 text-[#990F3D]" />
                      )}
                      {review.date && (
                        <span className="text-[10px] text-[#A89E94]">{review.date}</span>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-[#4A4540] leading-relaxed line-clamp-4">
                    {review.text}
                  </p>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
