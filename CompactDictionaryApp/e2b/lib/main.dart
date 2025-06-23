import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:google_fonts/google_fonts.dart';

void main() {
  runApp(DictionaryApp());
}

class DictionaryApp extends StatefulWidget {
  @override
  _DictionaryAppState createState() => _DictionaryAppState();
}

class _DictionaryAppState extends State<DictionaryApp> {
  final TextEditingController _controller = TextEditingController();
  Map<String, dynamic>? _result;
  String? _error;
  bool _darkMode = true;
  bool _loading = false;
  final FocusNode _searchFocusNode = FocusNode();

  final String apiBaseUrl =
      'https://compact-dictionary-api.onrender.com/api/dictionary/?word';

  Future<void> fetchDefinition(String word) async {
    if (word.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
      _searchFocusNode.unfocus();
    });

    try {
      final response = await http.get(
        Uri.parse('$apiBaseUrl$word'),
        headers: {'Accept': 'application/json'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(utf8.decode(response.bodyBytes));
        if (data == null || data['word'] == null) {
          throw Exception('No definition found');
        }
        setState(() {
          _result = data;
          _loading = false;
        });
      } else {
        throw Exception('Server error: ${response.statusCode}');
      }
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Widget _buildDefinitionItem(String text,
      {String? example, bool isBangla = false, int? index}) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Padding(
                padding: EdgeInsets.only(top: isBangla ? 8.0 : 4.0, right: 8.0),
                child: Icon(
                  Icons.circle,
                  size: 8,
                  color: _darkMode ? Colors.tealAccent : Colors.indigo,
                ),
              ),
              Expanded(
                child: Text(
                  text,
                  style: GoogleFonts.hindSiliguri(
                    fontSize: isBangla ? 18 : 16,
                    height: 1.5,
                  ),
                ),
              ),
            ],
          ),
          if (example != null && example.isNotEmpty)
            Padding(
              padding: EdgeInsets.only(left: 24.0, top: 4.0),
              child: Text(
                index != null ? '$index. $example' : '"$example"',
                style: GoogleFonts.hindSiliguri(
                  fontSize: 14,
                  fontStyle: FontStyle.italic,
                  color: _darkMode ? Colors.grey[400] : Colors.grey[600],
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildExamples(List<dynamic> examples) {
    if (examples.isEmpty) return SizedBox.shrink();

    return Padding(
      padding: EdgeInsets.only(left: 16.0, top: 8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Examples:',
            style: GoogleFonts.hindSiliguri(
              fontWeight: FontWeight.w500,
              fontSize: 16,
            ),
          ),
          SizedBox(height: 4),
          ...examples.asMap().entries.map((entry) {
            int idx = entry.key + 1;
            String example = entry.value;
            return Padding(
              padding: EdgeInsets.only(left: 8.0, top: 4.0),
              child: Text(
                '$idx. $example',
                style: GoogleFonts.hindSiliguri(
                  fontSize: 15,
                  fontStyle: FontStyle.italic,
                  color: _darkMode ? Colors.grey[400] : Colors.grey[600],
                ),
              ),
            );
          }).toList(),
        ],
      ),
    );
  }

  Widget _buildMeaningsSection(String title, List<dynamic> meanings) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: GoogleFonts.hindSiliguri(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: _darkMode ? Colors.tealAccent[400] : Colors.indigo,
          ),
        ),
        SizedBox(height: 8),
        ...meanings.map((meaning) {
          if (meaning is String) {
            return _buildDefinitionItem(meaning);
          } else if (meaning is Map) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (meaning['partOfSpeech'] != null)
                  Text(
                    meaning['partOfSpeech'],
                    style: GoogleFonts.hindSiliguri(
                      fontWeight: FontWeight.w500,
                      fontSize: 18,
                    ),
                  ),
                if (meaning['definitions'] != null)
                  ...(meaning['definitions'] as List).map((def) {
                    return _buildDefinitionItem(
                      def['definition'] ?? '',
                      example: def['example'],
                    );
                  }).toList(),
                if (meaning['examples'] != null &&
                    (meaning['examples'] as List).isNotEmpty)
                  _buildExamples(meaning['examples']),
              ],
            );
          }
          return SizedBox.shrink();
        }).toList(),
      ],
    );
  }

  Widget _buildPronunciationSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_result?['english']?['phonetic'] != null ||
            _result?['bangla']?['pronunciation'] != null)
          Padding(
            padding: EdgeInsets.only(bottom: 16),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_result?['english']?['phonetic'] != null)
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'English Pronunciation',
                          style: GoogleFonts.hindSiliguri(
                            fontSize: 16,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        Text(
                          '/${_result!['english']['phonetic']}/',
                          style: GoogleFonts.hindSiliguri(
                            fontSize: 18,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ),
                  ),
                if (_result?['bangla']?['pronunciation'] != null)
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Bangla Pronunciation',
                          style: GoogleFonts.hindSiliguri(
                            fontSize: 16,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        Text(
                          _result!['bangla']['pronunciation'],
                          style: GoogleFonts.hindSiliguri(
                            fontSize: 18,
                            fontStyle: FontStyle.italic,
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'E2E & E2B Dictionary',
      theme: _darkMode
          ? ThemeData.dark().copyWith(
              scaffoldBackgroundColor: Colors.grey[900],
              cardTheme: CardTheme(
                elevation: 2,
                margin: EdgeInsets.only(bottom: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            )
          : ThemeData.light().copyWith(
              cardTheme: CardTheme(
                elevation: 2,
                margin: EdgeInsets.only(bottom: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
            ),
      home: Scaffold(
        appBar: AppBar(
          title: Text('E2E & E2B DICTIONARY',
              style: GoogleFonts.hindSiliguri(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              )),
          actions: [
            IconButton(
              icon: Icon(_darkMode ? Icons.light_mode : Icons.dark_mode),
              onPressed: () => setState(() => _darkMode = !_darkMode),
            )
          ],
        ),
        body: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            children: [
              TextField(
                controller: _controller,
                decoration: InputDecoration(
                  hintText: 'Search for a word',
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  suffixIcon: IconButton(
                    icon: Icon(Icons.search),
                    onPressed: () => fetchDefinition(_controller.text.trim()),
                  ),
                ),
                onSubmitted: (value) => fetchDefinition(value.trim()),
                focusNode: _searchFocusNode,
              ),
              SizedBox(height: 20),
              Expanded(
                child: _loading
                    ? Center(child: CircularProgressIndicator())
                    : _error != null
                        ? Center(
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.error_outline,
                                    size: 48, color: Colors.red),
                                SizedBox(height: 16),
                                Text(
                                  _error!,
                                  style: TextStyle(fontSize: 18),
                                  textAlign: TextAlign.center,
                                ),
                              ],
                            ),
                          )
                        : _result == null
                            ? Center(
                                child: Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.search,
                                        size: 64, color: Colors.grey),
                                    SizedBox(height: 16),
                                    Text(
                                      'Search for any word',
                                      style: TextStyle(
                                          fontSize: 18, color: Colors.grey),
                                    ),
                                  ],
                                ),
                              )
                            : SingleChildScrollView(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      _result!['word']
                                              ?.toString()
                                              .toUpperCase() ??
                                          '',
                                      style: GoogleFonts.hindSiliguri(
                                        fontSize: 28,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                    SizedBox(height: 16),
                                    _buildPronunciationSection(),
                                    SizedBox(height: 16),
                                    // Show Bangla meanings first
                                    if (_result?['bangla']?['meanings'] != null)
                                      Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            'Bangla Meanings',
                                            style: GoogleFonts.hindSiliguri(
                                              fontSize: 20,
                                              fontWeight: FontWeight.w600,
                                              color: _darkMode
                                                  ? Colors.tealAccent[400]
                                                  : Colors.indigo,
                                            ),
                                          ),
                                          SizedBox(height: 8),
                                          ..._result!['bangla']['meanings']
                                              .map((meaning) =>
                                                  _buildDefinitionItem(
                                                    meaning,
                                                    isBangla: true,
                                                  ))
                                              .toList(),
                                          SizedBox(height: 24),
                                        ],
                                      ),
                                    // Then show English definitions
                                    if (_result?['english']?['meanings'] !=
                                        null)
                                      _buildMeaningsSection(
                                        'English Definitions',
                                        _result!['english']['meanings'],
                                      ),
                                    // Footer moved inside the scrollable content
                                    Padding(
                                      padding:
                                          EdgeInsets.only(top: 40, bottom: 20),
                                      child: Center(
                                        child: Text(
                                          '© All rights reserved to Ahsanul Anam Saboj',
                                          style: GoogleFonts.hindSiliguri(
                                            fontSize: 12,
                                            color: _darkMode
                                                ? Colors.grey[500]
                                                : Colors.grey[600],
                                          ),
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
