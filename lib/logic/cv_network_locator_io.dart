import 'dart:io';

Future<List<String>> discoverPrivateIpv4Prefixes() async {
  final Set<String> prefixes = <String>{};

  final List<NetworkInterface> interfaces = await NetworkInterface.list(
    type: InternetAddressType.IPv4,
    includeLinkLocal: false,
    includeLoopback: false,
  );

  for (final NetworkInterface iface in interfaces) {
    for (final InternetAddress address in iface.addresses) {
      final String ip = address.address;
      if (_isPrivateIpv4(ip)) {
        prefixes.add(_ipv4Prefix(ip));
      }
    }
  }

  return prefixes.toList(growable: false);
}

bool _isPrivateIpv4(String ip) {
  final List<String> parts = ip.split('.');
  if (parts.length != 4) {
    return false;
  }
  final int? a = int.tryParse(parts[0]);
  final int? b = int.tryParse(parts[1]);
  if (a == null || b == null) {
    return false;
  }
  return a == 10 ||
      (a == 172 && b >= 16 && b <= 31) ||
      (a == 192 && b == 168);
}

String _ipv4Prefix(String ip) => ip.split('.').take(3).join('.');