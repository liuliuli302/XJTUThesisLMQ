$ENV{'TZ'}='Asia/Shanghai';

use File::Find;
use File::Path qw(make_path);

$pdf_mode = 5;
$postscript_mode = 0;
$dvi_mode = 0;
$preview_mode = 0;
$cleanup_mode = 0;

$out_dir = "./Build";

sub ensure_output_subdirs {
  return unless defined $out_dir && $out_dir ne '';

  my %dirs;
  find(
    {
      wanted => sub {
        return unless -f $_ && /\.tex\z/;
        my $dir = $File::Find::dir;
        return if $dir eq '.';
        return if $dir eq $out_dir || index($dir, "$out_dir/") == 0;
        $dirs{$dir} = 1;
      },
    },
    '.'
  );

  for my $dir (sort keys %dirs) {
    make_path("$out_dir/$dir");
  }
}

ensure_output_subdirs();

$xelatex = "xelatex -synctex=1 -interaction=nonstopmode -file-line-error -shell-escape %O %S";
$biber = "biber %O %S";
$xdvipdfmx = 'xdvipdfmx -E -o %D %O %S';

add_cus_dep('glo', 'gls', 0, 'run_makeglossaries');
add_cus_dep('acn', 'acr', 0, 'run_makeglossaries');

sub run_makeglossaries {
  my ($base_name, $path) = fileparse( $_[0] );
  pushd $path;
  if ( $silent ) {
    my $return = system "makeglossaries -q $base_name";
  }
  else {
    my $return = system "makeglossaries $base_name";
  };
  popd;
  return $return;
}

push @generated_exts, 'glo', 'gls', 'glg';
push @generated_exts, 'acn', 'acr', 'alg';
push @generated_exts, 'synctex.gz';

$clean_ext = 'acn acr alg aux bbl bcf blg brf fdb_latexmk fls glg glo gls hd idx ilg ind ist lof log lot nav out run.xml thm toc toe dvi slg slo sls snm xdv xdy listing'