%global VER 6.9.12

Name:		ImageMagick
Version:	6.9.12.8
Release:	1%{?dist}
Summary:	An X application for displaying and manipulating images

License:	ImageMagick
Url:		http://www.imagemagick.org/
Source0:	%{name}-%{version}.tar.bz2

BuildRequires:	bzip2-devel, freetype-devel, libjpeg-devel, libpng-devel
BuildRequires:	libtiff-devel, giflib-devel, zlib-devel, perl-devel >= 5.8.1
BuildRequires:  libtool-ltdl-devel
BuildRequires:  libxml2-devel
BuildRequires:  librsvg-devel
BuildRequires:  libwebp-devel
BuildRequires:  autoconf automake gcc gcc-c++
BuildRequires:  fontconfig sailfish-fonts
BuildRequires:  make

Requires:	%{name}-libs = %{version}-%{release}

%description
ImageMagick is an image display and manipulation tool for the X
Window System. ImageMagick can read and write JPEG, TIFF, PNM, GIF,
and Photo CD image formats. It can resize, rotate, sharpen, color
reduce, or add special effects to an image, and when finished you can
either save the completed work in the original format or a different
one. ImageMagick also includes command line programs for creating
animated or transparent .gifs, creating composite images, creating
thumbnail images, and more.

ImageMagick is one of your choices if you need a program to manipulate
and display images. If you want to develop your own applications
which use ImageMagick code or APIs, you need to install
ImageMagick-devel as well.


%package devel
Summary:	Library links and header files for ImageMagick app development
Requires:	%{name} = %{version}-%{release}
Requires:	%{name}-libs = %{version}-%{release}

%description devel
ImageMagick-devel contains the library links and header files you'll
need to develop ImageMagick applications. ImageMagick is an image
manipulation program.

If you want to create applications that will use ImageMagick code or
APIs, you need to install ImageMagick-devel as well as ImageMagick.
You do not need to install it if you just want to use ImageMagick,
however.


%package libs
Summary: ImageMagick libraries to link with

%description libs
This packages contains a shared libraries to use within other applications.


%package perl
Summary: ImageMagick perl bindings
Requires: %{name}-libs = %{version}-%{release}
Requires: perl(:MODULE_COMPAT_%(eval "`%{__perl} -V:version`"; echo $version))

%description perl
Perl bindings to ImageMagick.

Install ImageMagick-perl if you want to use any perl scripts that use
ImageMagick.


%package c++
Summary: ImageMagick Magick++ library (C++ bindings)
Requires: %{name}-libs = %{version}-%{release}

%description c++
This package contains the Magick++ library, a C++ binding to the ImageMagick
graphics manipulation library.

Install ImageMagick-c++ if you want to use any applications that use Magick++.


%package c++-devel
Summary: C++ bindings for the ImageMagick library
Requires: %{name}-c++ = %{version}-%{release}
Requires: %{name}-devel = %{version}-%{release}

%description c++-devel
ImageMagick-devel contains the static libraries and header files you'll
need to develop ImageMagick applications using the Magick++ C++ bindings.
ImageMagick is an image manipulation program.

If you want to create applications that will use Magick++ code
or APIs, you'll need to install ImageMagick-c++-devel, ImageMagick-devel and
ImageMagick.
You don't need to install it if you just want to use ImageMagick, or if you
want to develop/compile applications using the ImageMagick C interface,
however.


%prep
%setup -n %{name}-%{version}/%{name}


%build
autoconf -f -i
# Reduce thread contention, upstream sets this flag for Linux hosts
export CFLAGS="%{optflags} -DIMPNG_SETJMP_IS_THREAD_SAFE"
%configure \
	--enable-shared \
	--disable-static \
	--with-modules \
	--with-perl \
	--with-x \
	--with-threads \
	--with-magick_plus_plus \
	--with-gslib \
	--with-wmf \
	--with-webp \
	--with-openexr \
	--with-rsvg \
	--with-xml \
	--with-perl-options="INSTALLDIRS=vendor %{?perl_prefix} CC='%__cc -L$PWD/magick/.libs' LDDLFLAGS='-shared -L$PWD/magick/.libs'" \
	--without-dps \
	--without-gcc-arch \
	--with-jbig \
	--with-openjp2 \
	--with-raw \
	--with-lqr \
	--with-gvc \
	--with-raqm

# Do *NOT* use %%{?_smp_mflags}, this causes PerlMagick to be silently misbuild
make


%install
%make_install
cp -a www/source %{buildroot}%{_datadir}/doc/%{name}-%{VER}

# perlmagick: fix perl path of demo files
%{__perl} -MExtUtils::MakeMaker -e 'MY->fixin(@ARGV)' PerlMagick/demo/*.pl

# perlmagick: cleanup various perl tempfiles from the build which get installed
find %{buildroot} -name "*.bs" |xargs rm -f
find %{buildroot} -name ".packlist" |xargs rm -f
find %{buildroot} -name "perllocal.pod" |xargs rm -f

# Do NOT remove .la files for codecs
# https://bugzilla.novell.com/show_bug.cgi?id=579798

# perlmagick: build files list
echo "%defattr(-,root,root,-)" > perl-pkg-files
find %{buildroot}/%{_libdir}/perl* -type f -print \
	| sed "s@^%{buildroot}@@g" > perl-pkg-files
find %{buildroot}%{perl_vendorarch} -type d -print \
	| sed "s@^%{buildroot}@%dir @g" \
	| grep -v '^%dir %{perl_vendorarch}$' \
	| grep -v '/auto$' >> perl-pkg-files
if [ -z perl-pkg-files ] ; then
	echo "ERROR: EMPTY FILE LIST"
	exit -1
fi

# fix multilib issues: Rename provided file with platform-bits in name.
# Create platform independant file inplace of provided and conditionally include required.
# $1 - filename.h to process.
function multilibFileVersions(){
mv $1 ${1%%.h}-%{__isa_bits}.h

local basename=$(basename $1)

cat >$1 <<EOF
#include <bits/wordsize.h>

#if __WORDSIZE == 32
# include "${basename%%.h}-32.h"
#elif __WORDSIZE == 64
# include "${basename%%.h}-64.h"
#else
# error "unexpected value for __WORDSIZE macro"
#endif
EOF
}

multilibFileVersions %{buildroot}%{_includedir}/%{name}-6/magick/magick-config.h
multilibFileVersions %{buildroot}%{_includedir}/%{name}-6/magick/magick-baseconfig.h
multilibFileVersions %{buildroot}%{_includedir}/%{name}-6/magick/version.h

rm -rf %{buildroot}/usr/share/doc
rm -rf %{buildroot}/usr/share/man


%check
export LD_LIBRARY_PATH=%{buildroot}/%{_libdir}
%make_build check || (cat test-suite.log && exit 1)
rm PerlMagick/demo/Generic.ttf

%post libs -p /sbin/ldconfig
%postun libs -p /sbin/ldconfig
%post c++ -p /sbin/ldconfig
%postun c++ -p /sbin/ldconfig

%files
%license LICENSE
%{_bindir}/[a-z]*

%files libs
%license LICENSE
%{_libdir}/libMagickCore-6.Q16.so.7*
%{_libdir}/libMagickWand-6.Q16.so.7*
%{_libdir}/%{name}-%{VER}
%{_datadir}/%{name}-6
%dir %{_sysconfdir}/%{name}-6
%config(noreplace) %{_sysconfdir}/%{name}-6/*.xml

%files devel
%{_bindir}/MagickCore-config
%{_bindir}/Magick-config
%{_bindir}/MagickWand-config
%{_bindir}/Wand-config
%{_libdir}/libMagickCore-6.Q16.so
%{_libdir}/libMagickWand-6.Q16.so
%{_libdir}/pkgconfig/MagickCore.pc
%{_libdir}/pkgconfig/MagickCore-6.Q16.pc
%{_libdir}/pkgconfig/ImageMagick.pc
%{_libdir}/pkgconfig/ImageMagick-6.Q16.pc
%{_libdir}/pkgconfig/MagickWand.pc
%{_libdir}/pkgconfig/MagickWand-6.Q16.pc
%{_libdir}/pkgconfig/Wand.pc
%{_libdir}/pkgconfig/Wand-6.Q16.pc
%dir %{_includedir}/%{name}-6
%{_includedir}/%{name}-6/magick
%{_includedir}/%{name}-6/wand

%files c++
%license www/Magick++/COPYING
%{_libdir}/libMagick++-6.Q16.so.9*

%files c++-devel
%{_bindir}/Magick++-config
%{_includedir}/%{name}-6/Magick++
%{_includedir}/%{name}-6/Magick++.h
%{_libdir}/libMagick++-6.Q16.so
%{_libdir}/pkgconfig/Magick++.pc
%{_libdir}/pkgconfig/Magick++-6.Q16.pc
%{_libdir}/pkgconfig/ImageMagick++.pc
%{_libdir}/pkgconfig/ImageMagick++-6.Q16.pc

%files perl -f perl-pkg-files

