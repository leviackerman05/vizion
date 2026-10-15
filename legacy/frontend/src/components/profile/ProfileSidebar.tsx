import { useEffect, useState } from "react";
import { User, BadgeDollarSign, BadgeCheck } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchMe, UserProfile } from "@/lib/api/user";
import { startCheckout } from "@/lib/api/payments";
import { PLANS } from "@/constants/strings";
import { toast } from "sonner";

const ProfileSidebar = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    fetchMe().then(setProfile).catch(console.error);
  }, []);

  const handleUpgrade = async () => {
    try {
      const url = await startCheckout();
      window.location.href = url;
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Checkout unavailable");
    }
  };

  return (
    <div className="w-full max-w-xs flex flex-col gap-4">
      <div className="flex flex-col items-center py-8">
        <div className="h-20 w-20 rounded-full bg-muted flex items-center justify-center mb-4">
          <User size={40} className="text-muted-foreground" />
        </div>
        <h2 className="text-lg font-medium">{profile?.email?.split("@")[0] || "User"}</h2>
        <p className="text-sm text-muted-foreground">{profile?.email || ""}</p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <BadgeDollarSign size={16} className="text-primary" />
            Subscription
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Plan</span>
            <span className="font-medium capitalize">{profile?.plan || PLANS.FREE}</span>
          </div>
          {profile?.plan === "free" && profile.remaining !== null && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Remaining today</span>
              <span className="font-medium">{profile.remaining} videos</span>
            </div>
          )}
          {profile?.plan !== "pro" && (
            <Button className="w-full gap-2 mt-2" onClick={handleUpgrade}>
              <BadgeCheck size={16} />
              {PLANS.UPGRADE}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ProfileSidebar;
