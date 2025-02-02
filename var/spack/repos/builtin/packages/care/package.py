# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack.package import *


class Care(CMakePackage, CudaPackage, ROCmPackage):
    """
    Algorithms for chai managed arrays.
    """

    homepage = "https://github.com/LLNL/CARE"
    git = "https://github.com/LLNL/CARE.git"
    tags = ["radiuss"]

    license("GPL-2.0-or-later")

    maintainers("adayton1")

    version("develop", branch="develop", submodules="True")
    version("master", branch="main", submodules="True")
    version(
        "0.13.1",
        tag="v0.13.1",
        commit="0fd0d47aaaa57076f26caad88e667fbc01ff7214",
        submodules="True",
    )
    version(
        "0.13.0",
        tag="v0.13.0",
        commit="2b288e2c557c3b14befeebc8e14a7d48348bd857",
        submodules="True",
    )
    version(
        "0.12.0",
        tag="v0.12.0",
        commit="a9978083035eb00a090451bd36d7987bc935204d",
        submodules="True",
    )
    version(
        "0.3.0", tag="v0.3.0", commit="5e2b69b2836c9f2215207ca9a36a690cb77eea33", submodules="True"
    )
    version(
        "0.2.0", tag="v0.2.0", commit="30135e03b14b1dc753634e9147dafede0663906f", submodules="True"
    )

    depends_on("c", type="build")  # generated
    depends_on("cxx", type="build")  # generated
    depends_on("fortran", type="build")  # generated

    variant("openmp", default=False, description="Build Shared Libs")
    variant(
        "implicit_conversions",
        default=True,
        description="Enable implicit" "conversions to/from raw pointers",
    )
    variant("benchmarks", default=True, description="Build benchmarks.")
    variant("examples", default=True, description="Build examples.")
    variant("docs", default=False, description="Build documentation")
    variant("tests", default=False, description="Build tests")
    variant("loop_fuser", default=False, description="Enable loop fusion capability")

    depends_on("cmake@3.8:", type="build")
    depends_on("cmake@3.9:", type="build", when="+cuda")
    depends_on("cmake@3.18:", type="build", when="@0.12.0:")
    depends_on("cmake@3.21:", type="build", when="@0.12.0:+rocm")

    depends_on("blt")
    depends_on("blt@0.6.2:", type="build", when="@0.13.0:")
    depends_on("blt@0.6.1:", type="build", when="@0.12.0:")
    depends_on("blt@0.4.0:", type="build", when="@0.3.1:")
    depends_on("blt@:0.3.6", type="build", when="@:0.3.0")
    conflicts("^blt@:0.3.6", when="+rocm")

    depends_on("camp", when="@:0.11.1")

    depends_on("umpire")
    depends_on("umpire@2024.02.1:", when="@0.13.0:")
    depends_on("umpire@2024.02.0:", when="@0.12.0:")

    depends_on("raja")
    depends_on("raja@2024.02.2:", when="@0.13.1:")
    depends_on("raja@2024.02.1:", when="@0.13.0:")
    depends_on("raja@2024.02.0:", when="@0.12.0:")

    depends_on("chai+enable_pick+raja")
    depends_on("chai@2024.02.2:", when="@0.13.1:")
    depends_on("chai@2024.02.1:", when="@0.13.0:")
    depends_on("chai@2024.02.0:", when="@0.12.0:")

    # pass on +cuda variants
    # WARNING: this package currently only supports an internal cub
    # package. This will cause a race condition if compiled with another
    # package that uses cub. TODO: have all packages point to the same external
    # cub package.
    depends_on("cub", when="+cuda")
    depends_on("camp+cuda", when="+cuda")
    depends_on("umpire+cuda~shared", when="+cuda")
    depends_on("raja+cuda~openmp", when="+cuda")
    depends_on("chai+cuda~shared", when="+cuda")

    # variants +rocm and amdgpu_targets are not automatically passed to
    # dependencies, so do it manually.
    depends_on("camp+rocm", when="+rocm")
    depends_on("umpire+rocm", when="+rocm")
    depends_on("raja+rocm~openmp", when="+rocm")
    depends_on("chai+rocm", when="+rocm")
    for val in ROCmPackage.amdgpu_targets:
        depends_on("camp amdgpu_target=%s" % val, when="amdgpu_target=%s" % val)
        depends_on("umpire amdgpu_target=%s" % val, when="amdgpu_target=%s" % val)
        depends_on("raja amdgpu_target=%s" % val, when="amdgpu_target=%s" % val)
        depends_on("chai amdgpu_target=%s" % val, when="amdgpu_target=%s" % val)

    conflicts("+openmp", when="+rocm")
    conflicts("+openmp", when="+cuda")

    def cmake_args(self):
        spec = self.spec
        from_variant = self.define_from_variant

        options = []
        options.append("-DBLT_SOURCE_DIR={0}".format(spec["blt"].prefix))

        if "+cuda" in spec:
            options.extend(
                [
                    "-DENABLE_CUDA=ON",
                    "-DCUDA_TOOLKIT_ROOT_DIR=" + spec["cuda"].prefix,
                    "-DNVTOOLSEXT_DIR=" + spec["cuda"].prefix,
                    "-DCUB_DIR=" + spec["cub"].prefix,
                ]
            )

            if not spec.satisfies("cuda_arch=none"):
                cuda_arch = spec.variants["cuda_arch"].value
                # Please note that within care, CUDA_ARCH is assigned to -code
                # and likewise CUDA_CODE is assigned to -arch, so these are
                # intentionally flipped here.
                options.append("-DCUDA_ARCH=sm_{0}".format(cuda_arch[0]))
                options.append("-DCUDA_CODE=compute_{0}".format(cuda_arch[0]))
        else:
            options.append("-DENABLE_CUDA=OFF")

        if "+rocm" in spec:
            options.extend(["-DENABLE_HIP=ON", "-DHIP_ROOT_DIR={0}".format(spec["hip"].prefix)])

            archs = self.spec.variants["amdgpu_target"].value
            if archs != "none":
                arch_str = ",".join(archs)
                options.append("-DHIP_HIPCC_FLAGS=--amdgpu-target={0}".format(arch_str))
        else:
            options.append("-DENABLE_HIP=OFF")

        options.extend(
            [
                from_variant("CARE_ENABLE_IMPLICIT_CONVERSIONS", "implicit_conversions"),
                from_variant("CARE_ENABLE_LOOP_FUSER", "loop_fuser"),
                self.define("CAMP_DIR", spec["camp"].prefix.share.camp.cmake),
                self.define("UMPIRE_DIR", spec["umpire"].prefix.share.umpire.cmake),
                self.define("RAJA_DIR", spec["raja"].prefix.share.raja.cmake),
                self.define("CHAI_DIR", spec["chai"].prefix.share.chai.cmake),
                from_variant("CARE_ENABLE_TESTS", "tests"),
            ]
        )

        # For tests to work, we also need BLT_ENABLE_TESTS to be on.
        # This will take care of the gtest dependency. CARE developers should
        # consider consolidating these flags in the future.
        options.append(from_variant("BLT_ENABLE_TESTS", "tests"))

        # There are both CARE_ENABLE_* and ENABLE_* variables in here because
        # one controls the BLT infrastructure and the other controls the CARE
        # infrastructure. The goal is to just be able to use the CARE_ENABLE_*
        # variables, but CARE isn't set up correctly for that yet.
        options.append(from_variant("ENABLE_BENCHMARKS", "benchmarks"))
        options.append(from_variant("CARE_ENABLE_BENCHMARKS", "benchmarks"))

        options.append(from_variant("ENABLE_EXAMPLES", "examples"))
        options.append(from_variant("CARE_ENABLE_EXAMPLES", "examples"))

        options.append(from_variant("ENABLE_DOCS", "docs"))
        options.append(from_variant("CARE_ENABLE_DOCS", "docs"))

        return options
