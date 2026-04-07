import 'dart:collection';
import 'dart:convert';
import 'dart:math';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'cv_network_locator.dart';

class CvDetectorClient {
  CvDetectorClient({http.Client? client}) : _client = client ?? http.Client();

  static const Duration _connectTimeout = Duration(seconds: 6);
  static const Duration _responseTimeout = Duration(seconds: 45);
  static Uri? _cachedBaseUri;

  final http.Client _client;

  void close() {
    _client.close();
  }

  Future<Uri> _resolveDetectUri() async {
    final String configuredBaseUrl = const String.fromEnvironment(
      'CV_BASE_URL',
      defaultValue: '',
    ).trim();

    if (configuredBaseUrl.isNotEmpty) {
      return Uri.parse('$configuredBaseUrl/detect');
    }

    final Uri? cached = _cachedBaseUri;
    if (cached != null) {
      return cached.resolve('/detect');
    }

    final List<Uri> candidates = await _buildCandidateBases();
    for (final List<Uri> batch in _chunkUris(candidates, 24)) {
      final List<Uri?> results = await Future.wait<Uri?>(
        batch.map(_probeBaseUri),
      );
      for (final Uri? found in results) {
        if (found != null) {
          _cachedBaseUri = found;
          return found.resolve('/detect');
        }
      }
    }

    // Android emulators cannot use localhost of host machine directly.
    final String fallbackBaseUrl =
        defaultTargetPlatform == TargetPlatform.android
        ? 'http://10.0.2.2:5000'
        : 'http://localhost:5000';
    return Uri.parse('$fallbackBaseUrl/detect');
  }

  Future<List<String>> detectIngredientsFromImageBytes({
    required List<int> imageBytes,
    String filename = 'capture.jpg',
  }) async {
    final Uri endpoint = await _resolveDetectUri();
    final http.MultipartRequest request = http.MultipartRequest('POST', endpoint)
      ..files.add(
        http.MultipartFile.fromBytes(
          'image',
          imageBytes,
          filename: filename,
        ),
      );

    http.StreamedResponse streamed;
    try {
      streamed = await _client.send(request).timeout(_connectTimeout);
    } catch (_) {
      throw Exception(_buildConnectionHelpMessage(endpoint));
    }

    final String body;
    try {
      body = await streamed.stream.bytesToString().timeout(_responseTimeout);
    } catch (_) {
      throw Exception('CV server took too long to respond.');
    }

    Map<String, dynamic> data;
    try {
      data = jsonDecode(body) as Map<String, dynamic>;
    } catch (_) {
      throw Exception('CV server returned invalid JSON.');
    }

    if (streamed.statusCode < 200 || streamed.statusCode >= 300) {
      final String message = (data['error'] as String?) ??
          'CV server request failed (${streamed.statusCode}).';
      throw Exception(message);
    }

    final bool success = data['success'] == true;
    if (!success) {
      final String message =
          (data['error'] as String?) ?? 'CV server could not detect ingredients.';
      throw Exception(message);
    }

    final Object? rawIngredients = data['ingredients'];
    if (rawIngredients is! List) {
      throw Exception('CV server response did not include ingredients list.');
    }

    final LinkedHashSet<String> normalized = LinkedHashSet<String>();
    for (final Object? item in rawIngredients) {
      final String value = (item as String?)?.trim() ?? '';
      if (value.isNotEmpty) {
        normalized.add(value);
      }
    }

    return normalized.toList(growable: false);
  }

  Future<List<Uri>> _buildCandidateBases() async {
    final Set<Uri> candidates = <Uri>{
      Uri.parse('http://127.0.0.1:5000'),
      Uri.parse('http://localhost:5000'),
      Uri.parse('http://10.0.2.2:5000'),
    };

    final List<String> prefixes = await discoverPrivateIpv4Prefixes();
    const List<int> preferredSuffixes = <int>[1, 2, 3, 10, 20, 30, 40, 50, 100, 101, 150, 200, 254];

    for (final String prefix in prefixes) {
      for (final int suffix in preferredSuffixes) {
        candidates.add(Uri.parse('http://$prefix.$suffix:5000'));
      }
      for (int suffix = 1; suffix <= 254; suffix++) {
        candidates.add(Uri.parse('http://$prefix.$suffix:5000'));
      }
    }

    return candidates.toList(growable: false);
  }

  List<List<Uri>> _chunkUris(List<Uri> uris, int chunkSize) {
    final List<List<Uri>> chunks = <List<Uri>>[];
    for (int i = 0; i < uris.length; i += chunkSize) {
      chunks.add(uris.sublist(i, min(i + chunkSize, uris.length)));
    }
    return chunks;
  }

  Future<Uri?> _probeBaseUri(Uri baseUri) async {
    final Uri healthUri = baseUri.resolve('/health');
    try {
      final http.Response response = await _client
          .get(healthUri)
          .timeout(const Duration(milliseconds: 450));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        return null;
      }
      final String body = response.body.toLowerCase();
      if (body.contains('running') || body.contains('ok')) {
        return baseUri;
      }
    } catch (_) {
      return null;
    }
    return null;
  }

  String _buildConnectionHelpMessage(Uri endpoint) {
    if (defaultTargetPlatform == TargetPlatform.android &&
        endpoint.host == '10.0.2.2') {
      return 'Cannot reach CV server from this Android device. '
          'If you are on a physical phone, run with '
          '--dart-define=CV_BASE_URL=http://<YOUR_PC_LAN_IP>:5000.';
    }
    return 'Could not connect to CV server at ${endpoint.toString()}.';
  }
}