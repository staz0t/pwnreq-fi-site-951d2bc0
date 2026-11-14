package main

import (
	"fmt"
	"os"

	sympb "github.com/bazel-contrib/bcr-frontend/build/stack/bazel/symbol/v1"
	"github.com/bazel-contrib/bcr-frontend/pkg/protoutil"
)

func main() {
	if len(os.Args) != 2 {
		panic("usage: readback FILE.pb.gz")
	}
	var message sympb.ModuleVersionSymbols
	if err := protoutil.ReadFile(os.Args[1], &message); err != nil {
		panic(err)
	}
	if len(message.File) != 1 || len(message.File[0].Symbol) != 1 {
		panic("unexpected protobuf shape")
	}
	marker := os.Getenv("EXPECTED_MARKER")
	moduleDoc := message.File[0].Description
	functionDoc := message.File[0].Symbol[0].Description
	if marker == "" || moduleDoc != marker+"_MODULE_DOCSTRING" || functionDoc != marker+"_FUNCTION_DOCSTRING" {
		panic("protobuf docstring mismatch")
	}
	fmt.Printf("module=%q version=%q source=%s\n", message.ModuleName, message.Version, message.Source)
	fmt.Printf("file=%q description=%q\n", message.File[0].Label.Name, moduleDoc)
	fmt.Printf("symbol=%q description=%q\n", message.File[0].Symbol[0].Name, functionDoc)
}
