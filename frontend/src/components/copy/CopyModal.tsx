"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, Info } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { createCopy, type Trader } from "@/lib/api";
import { useAuthStore } from "@/stores/auth-store";
import { useToast } from "@/hooks/use-toast";
import { formatAddress, formatPercent } from "@/lib/utils";

const copyFormSchema = z.object({
  allocation: z.number().min(10, "Minimum allocation is $10"),
  maxPositionSize: z.number().min(1).optional(),
  copyRatio: z.number().min(1).max(100),
  stopLossPercentage: z.number().min(1).max(100).optional(),
  autoCopyNew: z.boolean(),
  mirrorClose: z.boolean(),
  notifyOnCopy: z.boolean(),
});

type CopyFormValues = z.infer<typeof copyFormSchema>;

interface CopyModalProps {
  trader: Trader;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function CopyModal({ trader, isOpen, onClose, onSuccess }: CopyModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { token } = useAuthStore();
  const { toast } = useToast();

  const form = useForm<CopyFormValues>({
    resolver: zodResolver(copyFormSchema),
    defaultValues: {
      allocation: 100,
      copyRatio: 100,
      stopLossPercentage: 20,
      autoCopyNew: true,
      mirrorClose: false,
      notifyOnCopy: true,
    },
  });

  const copyRatio = form.watch("copyRatio");
  const allocation = form.watch("allocation");

  const onSubmit = async (data: CopyFormValues) => {
    if (!token) {
      toast({
        title: "Authentication required",
        description: "Please connect your wallet first.",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await createCopy(
        {
          trader_address: trader.wallet_address,
          allocation: data.allocation.toString(),
          max_position_size: data.maxPositionSize?.toString(),
          copy_ratio: data.copyRatio.toString(),
          stop_loss_percentage: data.stopLossPercentage?.toString(),
          auto_copy_new: data.autoCopyNew,
          mirror_close: data.mirrorClose,
          notify_on_copy: data.notifyOnCopy,
        },
        token
      );

      toast({
        title: "Copy started!",
        description: `You are now copying ${formatAddress(trader.wallet_address)}`,
      });

      onSuccess?.();
      onClose();
    } catch (error) {
      toast({
        title: "Failed to start copy",
        description: error instanceof Error ? error.message : "Unknown error",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <DialogHeader>
            <DialogTitle>Copy Trader</DialogTitle>
            <DialogDescription>
              Configure how you want to copy{" "}
              <span className="font-semibold">
                {formatAddress(trader.wallet_address)}
              </span>
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Allocation */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="allocation">Allocation (USDC)</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent id="allocation-tooltip">
                      Total amount you want to allocate for copying this trader
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <Input
                id="allocation"
                type="number"
                disabled={isLoading}
                aria-describedby="allocation-tooltip"
                {...form.register("allocation", { valueAsNumber: true })}
              />
              {form.formState.errors.allocation && (
                <p
                  className="text-sm text-destructive"
                  role="alert"
                  aria-live="polite"
                >
                  {form.formState.errors.allocation.message}
                </p>
              )}
            </div>

            {/* Copy Ratio */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Copy Ratio: {copyRatio}%</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      <p>
                        Percentage of the trader&apos;s position size you want to copy.
                        At 100%, if they invest 10% of their portfolio, you invest
                        10% of your allocation.
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <Slider
                value={[copyRatio]}
                onValueChange={([value]) => form.setValue("copyRatio", value)}
                min={1}
                max={100}
                step={1}
                disabled={isLoading}
              />
              <div className="text-sm text-muted-foreground">
                If trader invests 10% of portfolio with ${allocation} allocation:
                <span className="font-semibold text-foreground ml-1">
                  ${((allocation * 0.1 * copyRatio) / 100).toFixed(2)}
                </span>
              </div>
            </div>

            {/* Max Position Size */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="maxPositionSize">Max Position Size (USDC)</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      Maximum amount for any single copied position
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <Input
                id="maxPositionSize"
                type="number"
                placeholder="Optional"
                disabled={isLoading}
                {...form.register("maxPositionSize", { valueAsNumber: true })}
              />
            </div>

            {/* Stop Loss */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="stopLossPercentage">Stop Loss (%)</Label>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger>
                      <Info className="h-4 w-4 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      Automatically close positions when loss reaches this percentage
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
              <Input
                id="stopLossPercentage"
                type="number"
                placeholder="Optional"
                disabled={isLoading}
                {...form.register("stopLossPercentage", { valueAsNumber: true })}
              />
            </div>

            {/* Toggle Options */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto Copy New Trades</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically copy new positions
                  </p>
                </div>
                <Switch
                  checked={form.watch("autoCopyNew")}
                  onCheckedChange={(checked) =>
                    form.setValue("autoCopyNew", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Mirror Close</Label>
                  <p className="text-sm text-muted-foreground">
                    Close when trader closes
                  </p>
                </div>
                <Switch
                  checked={form.watch("mirrorClose")}
                  onCheckedChange={(checked) =>
                    form.setValue("mirrorClose", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified on copied trades
                  </p>
                </div>
                <Switch
                  checked={form.watch("notifyOnCopy")}
                  onCheckedChange={(checked) =>
                    form.setValue("notifyOnCopy", checked)
                  }
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Start Copying
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
