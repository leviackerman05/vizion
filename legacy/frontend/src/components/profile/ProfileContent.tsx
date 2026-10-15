import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BadgeCheck } from "lucide-react";
import { startCheckout, openBillingPortal } from "@/lib/api/payments";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { fetchMe, UserProfile } from "@/lib/api/user";

const ProfileContent = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    fetchMe().then(setProfile).catch(console.error);
    const params = new URLSearchParams(window.location.search);
    if (params.get("checkout") === "success") {
      toast.success("Welcome to Pro! Your plan has been upgraded.");
      fetchMe().then(setProfile);
    }
  }, []);

  const handleSubscribe = async () => {
    try {
      const url = await startCheckout();
      window.location.href = url;
    } catch (err) {
      toast.error(
        err instanceof Error
          ? err.message
          : "Stripe not configured. Add STRIPE_SECRET_KEY and STRIPE_PRICE_ID to .env"
      );
    }
  };

  const handlePortal = async () => {
    try {
      const url = await openBillingPortal();
      window.location.href = url;
    } catch {
      toast.error("No billing account found");
    }
  };

  return (
    <div className="flex-1 p-6">
      <Tabs defaultValue="subscription" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="subscription">Subscription</TabsTrigger>
          <TabsTrigger value="billing">Billing</TabsTrigger>
        </TabsList>

        <TabsContent value="subscription" className="space-y-4">
          <h2 className="text-xl font-semibold">Plans</h2>
          <div className="grid md:grid-cols-2 gap-4 max-w-2xl">
            <Card className={`p-6 ${profile?.plan === "free" ? "border-primary" : ""}`}>
              <h3 className="font-medium mb-1">Free</h3>
              <p className="text-2xl font-bold mb-4">$0<span className="text-sm font-normal text-muted-foreground">/mo</span></p>
              <ul className="space-y-2 text-sm text-muted-foreground mb-4">
                <li className="flex gap-2"><BadgeCheck size={14} className="text-primary mt-0.5" />5 videos per day</li>
                <li className="flex gap-2"><BadgeCheck size={14} className="text-primary mt-0.5" />480p quality</li>
              </ul>
              {profile?.plan === "free" && (
                <Button variant="outline" className="w-full" disabled>Current plan</Button>
              )}
            </Card>

            <Card className={`p-6 border-2 ${profile?.plan === "pro" ? "border-primary" : "border-primary/30"}`}>
              <h3 className="font-medium mb-1">Pro</h3>
              <p className="text-2xl font-bold mb-4">$19<span className="text-sm font-normal text-muted-foreground">/mo</span></p>
              <ul className="space-y-2 text-sm text-muted-foreground mb-4">
                <li className="flex gap-2"><BadgeCheck size={14} className="text-primary mt-0.5" />Unlimited videos</li>
                <li className="flex gap-2"><BadgeCheck size={14} className="text-primary mt-0.5" />1080p HD quality</li>
                <li className="flex gap-2"><BadgeCheck size={14} className="text-primary mt-0.5" />Export & download</li>
              </ul>
              {profile?.plan === "pro" ? (
                <Button variant="outline" className="w-full" onClick={handlePortal}>
                  Manage subscription
                </Button>
              ) : (
                <Button className="w-full gap-2" onClick={handleSubscribe}>
                  <BadgeCheck size={16} />
                  Subscribe (test mode)
                </Button>
              )}
            </Card>
          </div>
          <p className="text-xs text-muted-foreground">
            Uses Stripe test mode — no real charges. Test card: 4242 4242 4242 4242
          </p>
        </TabsContent>

        <TabsContent value="billing">
          <Card className="p-6 max-w-lg">
            <p className="text-sm text-muted-foreground mb-4">
              {profile?.plan === "pro"
                ? "Manage your subscription and billing details."
                : "Upgrade to Pro to access billing history."}
            </p>
            {profile?.plan === "pro" ? (
              <Button onClick={handlePortal}>Open billing portal</Button>
            ) : (
              <Button onClick={handleSubscribe}>Upgrade to Pro</Button>
            )}
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ProfileContent;
