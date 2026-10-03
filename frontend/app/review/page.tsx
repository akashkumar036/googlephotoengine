"use client";
import React, { useEffect, useState } from "react";
import {
  CheckSquare,
  Check,
  X,
  Edit3,
  Bookmark,
  AlertOctagon,
  Sparkles,
  Layers,
  FolderPlus,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import { ApiService } from "@/lib/api";
import { Card, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Tabs } from "@/components/ui/Tabs";
import { Skeleton, EmptyState } from "@/components/ui/EmptyState";

export default function HumanReviewPage() {
  const [activeTab, setActiveTab] = useState("queue");
  const [queueItems, setQueueItems] = useState<any[]>([]);
  const [clusters, setClusters] = useState<any[]>([]);
  const [taxonomyData, setTaxonomyData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editingConvId, setEditingConvId] = useState<string | null>(null);
  const [editedIntent, setEditedIntent] = useState("");
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const loadAll = async () => {
    setIsLoading(true);
    try {
      const [qRes, cRes, tRes] = await Promise.all([
        ApiService.getReviewQueue({ limit: 50 }).catch(() => ({ items: [] })),
        ApiService.getClusters().catch(() => ({ data: [] })),
        ApiService.getTaxonomyReview().catch(() => ({ proposals: [], predefined_categories: [] })),
      ]);
      setQueueItems(qRes?.items || []);
      setClusters(cRes?.data || []);
      setTaxonomyData(tRes);
    } catch (err) {
      console.error("Failed to load review data", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleReviewAction = async (conversationId: string, action: string, updates: Record<string, any> = {}) => {
    try {
      await ApiService.submitReview({
        conversation_id: conversationId,
        action,
        intent: updates.intent,
        is_relevant: updates.is_relevant,
        notes: updates.notes || `Researcher applied action: ${action}`,
      });

      // Remove from queue locally
      setQueueItems((prev) => prev.filter((item) => item.conversation_id !== conversationId));
      setEditingConvId(null);
      setActionSuccessMsg(`Review recorded: action '${action}' saved to database.`);
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (err: any) {
      alert("Failed to submit review: " + (err?.response?.data?.detail || err.message));
    }
  };

  const handleClusterRename = async (clusterId: string) => {
    const newName = prompt("Enter new curated label for this cluster:");
    if (!newName || !newName.trim()) return;
    try {
      await ApiService.handleClusterAction(clusterId, "rename", { new_name: newName.trim() });
      setClusters((prev) =>
        prev.map((c) => (c.id === clusterId ? { ...c, label: newName.trim() } : c))
      );
      setActionSuccessMsg("Cluster label updated successfully.");
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (err: any) {
      alert("Failed to rename cluster: " + (err?.response?.data?.detail || err.message));
    }
  };

  const handleProposalAction = async (proposalId: string, action: "approve" | "reject") => {
    try {
      await ApiService.handleProposalAction(proposalId, action, `Researcher decision: ${action}`);
      if (taxonomyData?.proposals) {
        setTaxonomyData({
          ...taxonomyData,
          proposals: taxonomyData.proposals.map((p: any) =>
            p.id === proposalId
              ? { ...p, is_approved: action === "approve", is_rejected: action === "reject" }
              : p
          ),
        });
      }
      setActionSuccessMsg(`Proposal marked as ${action}d.`);
      setTimeout(() => setActionSuccessMsg(null), 3000);
    } catch (err: any) {
      alert("Failed to update proposal: " + (err?.response?.data?.detail || err.message));
    }
  };

  const tabs = [
    { id: "queue", label: "Classification Queue", count: queueItems.length },
    { id: "clusters", label: "Cluster Curation", count: clusters.length },
    { id: "taxonomy", label: "Taxonomy Proposals", count: taxonomyData?.proposals?.filter((p: any) => !p.is_approved && !p.is_rejected)?.length || 0 },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-16">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white sm:text-3xl">
              Human Review & Curation
            </h1>
            <Badge variant="indigo" size="sm">HITL Feedback Loop</Badge>
          </div>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Audit AI classifications, correct low-confidence annotations, curate semantic clusters, and approve new retrieval taxonomy proposals.
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={loadAll}
          icon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />}
        >
          Refresh
        </Button>
      </div>

      {actionSuccessMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2 animate-in fade-in">
          <Check className="w-4 h-4 flex-shrink-0" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}

      {/* Tabs */}
      <Tabs tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab 1: Review Queue */}
      {activeTab === "queue" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 px-1">
            <span>{queueItems.length} items awaiting human review (ordered by lowest confidence first)</span>
          </div>

          {isLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-48 w-full" />
              ))}
            </div>
          ) : queueItems.length === 0 ? (
            <EmptyState
              title="All items reviewed!"
              description="No pending classifications requiring human review in the active queue."
            />
          ) : (
            <div className="space-y-4">
              {queueItems.map((item) => {
                const isEditing = editingConvId === item.conversation_id;
                const ai = item.ai_classification || {};

                return (
                  <Card key={item.conversation_id} className="p-6 space-y-4">
                    {/* Header */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800">
                      <div className="flex items-center gap-2">
                        <Badge variant="default" size="sm">{item.source?.toUpperCase() || "SOURCE"}</Badge>
                        {item.is_demo && <Badge variant="demo">DEMO DATA</Badge>}
                        <span className="text-xs font-mono text-slate-500">{item.conversation_id.slice(0, 8)}...</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-slate-400">AI Confidence:</span>
                        <span className={`text-xs font-bold ${ai.confidence < 0.7 ? "text-amber-400" : "text-emerald-400"}`}>
                          {Math.round((ai.confidence || 0) * 100)}%
                        </span>
                      </div>
                    </div>

                    {/* Excerpt */}
                    <p className="text-xs text-slate-200 bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 font-mono leading-relaxed max-h-36 overflow-y-auto">
                      {item.text}
                    </p>

                    {/* Current Classification Values */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs bg-slate-950/40 p-3.5 rounded-xl border border-slate-800/60">
                      <div>
                        <span className="text-slate-500 block mb-1">Primary Intent:</span>
                        {isEditing ? (
                          <select
                            value={editedIntent}
                            onChange={(e) => setEditedIntent(e.target.value)}
                            className="bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-xs text-white"
                          >
                            <option value="find_photo">find_photo</option>
                            <option value="find_video">find_video</option>
                            <option value="find_screenshot">find_screenshot</option>
                            <option value="cleanup_duplicates">cleanup_duplicates</option>
                            <option value="album_organization">album_organization</option>
                          </select>
                        ) : (
                          <span className="font-semibold text-white">{ai.primary_intent || "Unclassified"}</span>
                        )}
                      </div>

                      <div>
                        <span className="text-slate-500 block mb-1">Memory Dimensions:</span>
                        <div className="flex flex-wrap gap-1">
                          {(ai.memory_types || []).map((m: string, idx: number) => (
                            <Badge key={idx} variant="purple" size="sm">{m}</Badge>
                          ))}
                        </div>
                      </div>

                      <div>
                        <span className="text-slate-500 block mb-1">Failure Modes:</span>
                        <div className="flex flex-wrap gap-1">
                          {(ai.failure_modes || []).map((f: string, idx: number) => (
                            <Badge key={idx} variant="rose" size="sm">{f.replace("_", " ")}</Badge>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Action Bar */}
                    <div className="pt-2 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        {isEditing ? (
                          <>
                            <Button
                              size="sm"
                              variant="primary"
                              onClick={() =>
                                handleReviewAction(item.conversation_id, "correct", { intent: editedIntent })
                              }
                            >
                              Save Correction
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => setEditingConvId(null)}>
                              Cancel
                            </Button>
                          </>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingConvId(item.conversation_id);
                              setEditedIntent(ai.primary_intent || "find_photo");
                            }}
                            icon={<Edit3 className="w-3.5 h-3.5" />}
                          >
                            Correct
                          </Button>
                        )}

                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            handleReviewAction(item.conversation_id, "invalidate", { is_relevant: false })
                          }
                          icon={<AlertOctagon className="w-3.5 h-3.5 text-rose-400" />}
                        >
                          Mark Irrelevant
                        </Button>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="secondary"
                          onClick={() => handleReviewAction(item.conversation_id, "bookmark")}
                          icon={<Bookmark className="w-3.5 h-3.5" />}
                        >
                          Bookmark
                        </Button>
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleReviewAction(item.conversation_id, "approve")}
                          icon={<Check className="w-3.5 h-3.5" />}
                        >
                          Approve AI Annotation
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Clusters Curation */}
      {activeTab === "clusters" && (
        <Card className="p-6 space-y-4">
          <CardHeader>
            <div>
              <CardTitle>Semantic Clusters Management</CardTitle>
              <p className="text-xs text-slate-400">Curate AI-generated cluster labels or merge related topic clusters</p>
            </div>
          </CardHeader>

          {clusters.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-8">No semantic clusters formed yet.</p>
          ) : (
            <div className="divide-y divide-slate-800">
              {clusters.map((cl) => (
                <div key={cl.id} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-white">{cl.label || "Untitled Cluster"}</h4>
                      <Badge variant="indigo" size="sm">{cl.member_count || 0} members</Badge>
                      {cl.is_archived && <Badge variant="rose" size="sm">Archived</Badge>}
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-1">{cl.description || "Synthesized DBSCAN cluster"}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" onClick={() => handleClusterRename(cl.id)}>
                      Rename
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Tab 3: Taxonomy Proposals */}
      {activeTab === "taxonomy" && (
        <Card className="p-6 space-y-6">
          <div>
            <CardTitle>Taxonomy Proposals</CardTitle>
            <p className="text-xs text-slate-400 mt-1">
              New problem categories surfaced by outlier discovery or unknown-unknowns detection requiring researcher approval.
            </p>
          </div>

          {(!taxonomyData?.proposals || taxonomyData.proposals.length === 0) ? (
            <p className="text-xs text-slate-500 text-center py-8">No pending taxonomy proposals.</p>
          ) : (
            <div className="space-y-3">
              {taxonomyData.proposals.map((prop: any) => (
                <div key={prop.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-white">{prop.category_name}</span>
                    <div className="flex items-center gap-2">
                      {prop.is_approved ? (
                        <Badge variant="emerald" size="sm">Approved</Badge>
                      ) : prop.is_rejected ? (
                        <Badge variant="rose" size="sm">Rejected</Badge>
                      ) : (
                        <Badge variant="amber" size="sm">Pending Approval</Badge>
                      )}
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">
                    {prop.description || "Proposed category based on semantic outlier clustering."}
                  </p>
                  {!prop.is_approved && !prop.is_rejected && (
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800/80">
                      <Button size="sm" variant="danger" onClick={() => handleProposalAction(prop.id, "reject")}>
                        Reject
                      </Button>
                      <Button size="sm" variant="primary" onClick={() => handleProposalAction(prop.id, "approve")}>
                        Approve Category
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
