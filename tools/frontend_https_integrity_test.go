package bcr

import (
	"os"
	"strings"
	"testing"

	bzpb "github.com/bazel-contrib/bcr-frontend/build/stack/bazel/registry/v1"
)

func TestControlledHttpsSourceDropsReviewedIntegrity(t *testing.T) {
	url := os.Getenv("SOURCE_URL")
	integrity := os.Getenv("SOURCE_INTEGRITY")
	if !strings.HasPrefix(url, "https://") || integrity == "" {
		t.Fatal("missing controlled HTTPS source input")
	}
	module := &bzpb.ModuleVersion{Name: "proof", Version: "1.0.0"}
	label := makeBzlRepositoryModulesLabel(module.Name, module.Version)
	makeRule := func(rawURL string) string {
		source := &bzpb.ModuleSource{Url: rawURL, Integrity: integrity}
		return makeBzlRepository(label, module, source).AttrString("sha256")
	}
	want, ok := getSha256Integrity(integrity)
	if !ok || want == "" {
		t.Fatal("reviewed integrity is not SHA-256")
	}
	if got := makeRule(strings.Replace(url, "https://", "http://", 1)); got != want {
		t.Fatalf("HTTP control sha256 = %q, want %q", got, want)
	}
	if got := makeRule(url); got != "" {
		t.Fatalf("HTTPS attack sha256 = %q, want empty", got)
	}
}
